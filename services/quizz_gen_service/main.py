from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from .cache import redis_client
from .model import quizz_generator
from .data_models import QuizzRequest, User, SubmitAnswers
import hashlib
import json
from .auth_client import get_current_active_user
from .logging_config import get_logger
import uuid
from datetime import datetime
from fastapi import BackgroundTasks
from .quizz_settings import quizz_settings
from typing import cast, Tuple, List
from .persistence import store_quizz
from .db import create_db_and_tables
from contextlib import asynccontextmanager


# Initialize the logger for this module
logger = get_logger(__name__)


app = FastAPI(title="Quiz Generation Service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating Quizz tables...")
    create_db_and_tables()
    logger.info("Quizz tables created. Service is ready.")
    yield


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    rabbit = "disabled"
    try:
        if quizz_settings.RABBITMQ_URL:
            import aio_pika  # local import to avoid startup hard dep

            conn = await aio_pika.connect_robust(quizz_settings.RABBITMQ_URL)
            await conn.close()
            rabbit = "ok"
    except Exception:
        rabbit = "error"
    return {
        "status": "healthy",
        "service": "Quiz Generation Service",
        "rabbitmq": rabbit,
    }


@app.post("/generate-quiz")
def generate_quizz(
    request: QuizzRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        quizz = quizz_generator(
            request.topic,
            request.num_questions,
            request.difficulty,
            request.style,
        )
        logger.info(f"Quizz generated: {quizz}")
        store_quizz(
            username=current_user.username,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            style=request.style,
            questions=quizz["questions"],
            tags=quizz["tags"],
        )
        logger.info(f"Quizz stored: {quizz}")
        quizz_str = json.dumps(
            {"questions": quizz["questions"], "tags": quizz["tags"]},
            sort_keys=True,
        )
        quizz_hash = hashlib.sha256(quizz_str.encode()).hexdigest()
        cache_key = f"quizz_request:{current_user.username}:{quizz_hash}"
        redis_client.setex(cache_key, 3600, quizz_str)
        logger.info(f"Quizz cached: {quizz_str}, key: {cache_key}")

        return {"quizz_questions": quizz["questions"], "tags": quizz["tags"]}

    except Exception as e:
        logger.error(f"Quizz generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quizz generation failed: {str(e)}",
        )


@app.post("/create-quiz")
def create_quiz(
    request: QuizzRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        questions = quizz_generator(
            request.topic,
            request.num_questions,
            request.difficulty,
            request.style,
        )
        store_quizz(
            username=current_user.username,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            style=request.style,
            questions=questions["questions"],
            tags=questions["tags"],
        )
        logger.info(f"Quizz stored: {questions}")
        quiz_id = str(uuid.uuid4())
        key = f"Quiz:{current_user.username}:{quiz_id}"
        # keep for 1 hour
        redis_client.setex(key, 3600, json.dumps(questions))
        return {"quiz_id": quiz_id, "questions": questions["questions"], "tags": questions["tags"]}
    except Exception as e:
        logger.error(f"Create quiz failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create quiz failed: {str(e)}",
        )


@app.post("/submit-answers", status_code=202)
async def submit_answers(
    payload: SubmitAnswers,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        key = f"Quiz:{current_user.username}:{payload.quiz_id}"
        data = redis_client.get(key)
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found or expired",
            )
        # Aceita tanto o formato novo {"status":"done","questions":[...]}
        # como o legado que guardava apenas a lista de perguntas.
        parsed = json.loads(cast(str, data))
        if isinstance(parsed, dict) and "questions" in parsed:
            questions = parsed["questions"]
        else:
            questions = parsed
        if not isinstance(questions, list):
            raise HTTPException(
                status_code=400,
                detail="Invalid quiz content",
            )
        logger.info(
            "Submit answers check: quiz_id=%s q_len=%s a_len=%s",
            payload.quiz_id,
            len(questions),
            len(payload.answers),
        )
        if len(payload.answers) != len(questions):
            raise HTTPException(
                status_code=400,
                detail="Answers count mismatch",
            )

        job_id = str(uuid.uuid4())
        payload_msg = {
            "job_id": job_id,
            "username": current_user.username,
            "student_id": current_user.username,
            "quizz_questions": questions,
            "student_answers": payload.answers,
            "created_at": datetime.utcnow().isoformat(),
        }

        async def _do_publish_eval(p):
            try:
                # publicar em background para não bloquear a resposta 202
                from .mq import _publish_with_retry, quizz_settings

                await _publish_with_retry(
                    p,
                    quizz_settings.RABBITMQ_ROUTING_KEY,
                )
            except Exception as e:
                logger.error("Evaluation publish failed (bg): %s", e)

        background_tasks.add_task(_do_publish_eval, payload_msg)
        return {"job_id": job_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Submit answers failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submit answers failed: {str(e)}",
        )


@app.post("/generate-async", status_code=202)
def generate_quizz_async(
    request: QuizzRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Marca o job como 'queued' e agenda a publicação no RabbitMQ
    em segundo plano. Assim a resposta 202 é imediata, reduzindo
    5xx por timeouts de rede ao broker.
    """
    job_id = str(uuid.uuid4())
    quizz_id = job_id
    key = f"Quizz:{current_user.username}:{quizz_id}"
    # marca como queued no Redis
    redis_client.setex(key, 3600, json.dumps({"status": "queued"}))
    payload = {
        "quiz_id": quizz_id,
        "username": current_user.username,
        "topic": request.topic,
        "num_questions": request.num_questions,
        "difficulty": request.difficulty,
        "style": request.style,
        "created_at": datetime.utcnow().isoformat(),
    }

    async def _do_publish(p):
        try:
            await publish_quiz_generate(p)
        except Exception as e:
            logger.error(f"Quizz async publish failed (bg): {e}")
            # manter "queued" para permitir retries externos/novas tentativas

    async def publish_quiz_generate(p):
        # usa versão assíncrona interna do publisher para evitar
        # bloquear worker
        from .mq import _publish_with_retry, quizz_settings

        await _publish_with_retry(
            p,
            quizz_settings.RABBITMQ_ROUTING_KEY_GENERATE,
        )

    # agenda publicação em background (não bloqueia response)
    background_tasks.add_task(_do_publish, payload)
    return {"quizz_id": quizz_id, "status": "queued"}


@app.get("/jobs/{quizz_id}")
def get_quiz_job_status(
    quizz_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        key = f"Quizz:{current_user.username}:{quizz_id}"
        val = redis_client.get(key)
        if not val:
            # Ainda a processar (evitar 5xx para não inflacionar erros)
            return {"status": "processing"}
        try:
            data = json.loads(cast(str, val))
            return data
        except Exception:
            # Se o valor já é uma lista/str serializada,
            # devolva como concluído
            return {
                "status": "done",
                "questions": val,
            }
    except Exception as e:
        # Erro transitório de Redis/rede → tratar como em processamento
        return {
            "status": "processing",
            "error": str(e),
        }


@app.get("/get-quizz-questions")
def get_questions(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        matching_keys = []
        cursor = 0  # Start with cursor 0

        # Executa ao menos um SCAN e termina quando o cursor voltar a 0
        while True:
            cursor, keys = cast(
                Tuple[int, List[str]],
                redis_client.scan(
                    cursor=cursor,
                    match=(f"quizz_request:{current_user.username}:*"),
                    count=100,
                ),
            )
            matching_keys.extend(keys)
            if cursor == 0:
                break

        # Retrieve all the values for the found keys
        if matching_keys:
            values = redis_client.mget(matching_keys)
            logger.info(f"Values: {values}")
            return values
        else:
            logger.info("No keys found for the pattern.")
            return "No keys found for the pattern."

    except Exception as e:
        logger.error(f"Failed to get quizz questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quizz questions: {str(e)}",
        )
