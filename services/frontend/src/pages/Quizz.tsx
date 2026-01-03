import { useState } from "react";
import { api } from "../api";

export default function Quizz() {
  // Passo 1: gerar quiz
  const [topic, setTopic] = useState("math");
  const [num, setNum] = useState(3);
  const [difficulty, setDifficulty] = useState("easy");
  const [style, setStyle] = useState("concise");

  const [quizId, setQuizId] = useState<string>("");
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);

  // Passo 2: submeter respostas → job_id
  const [job, setJob] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);

  async function generateAsync() {
    setErr(null);
    setJob("");
    setQuizId("");
    setQuestions([]);
    setAnswers([]);
    try {
      const body = {
        topic,
        num_questions: num,
        difficulty,
        style,
      };
      const { data } = await api.post("/quiz/generate-async", body, {
        headers: { "Content-Type": "application/json" },
      });
      setQuizId(data?.quiz_id || "");
      const qs: string[] = Array.isArray(data?.questions) ? data.questions : [];
      setQuestions(qs);
      setAnswers(qs.map(() => ""));
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? e?.message ?? "Erro a gerar quiz");
    }
  }

  async function submitAnswers() {
    setErr(null);
    setJob("");
    try {
      const body = { quiz_id: quizId, answers };
      const { data } = await api.post("/quiz/submit-answers", body, {
        headers: { "Content-Type": "application/json" },
      });
      setJob(data?.job_id ?? "");
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? e?.message ?? "Erro a submeter respostas");
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Quizz → Geração e Avaliação (assíncrono)</h2>

      {!quizId && (
        <div style={{ marginBottom: 16 }}>
          <h4>Gerar Quiz</h4>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="topic" />
            <input
              type="number"
              value={num}
              min={1}
              max={10}
              onChange={(e) => setNum(parseInt(e.target.value || "1", 10))}
              placeholder="num_questions"
            />
            <input value={difficulty} onChange={(e) => setDifficulty(e.target.value)} placeholder="difficulty" />
            <input value={style} onChange={(e) => setStyle(e.target.value)} placeholder="style" />
            <button onClick={generateAsync}>Gerar Quiz (async)</button>
          </div>
        </div>
      )}

      {err && <div style={{ color: "red", marginBottom: 8 }}>{err}</div>}

      {quizId && (
        <div>
          <div style={{ marginBottom: 8 }}>
            Quiz ID: <code>{quizId}</code>
          </div>
          {questions.map((q, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <div><strong>Pergunta {idx + 1}:</strong> {q}</div>
              <input
                style={{ width: 480 }}
                value={answers[idx]}
                onChange={(e) => {
                  const next = [...answers];
                  next[idx] = e.target.value;
                  setAnswers(next);
                }}
                placeholder="Resposta"
              />
            </div>
          ))}
          <button onClick={submitAnswers} disabled={!answers.length}>
            Submeter Respostas
          </button>
        </div>
      )}

      {job && (
        <div style={{ marginTop: 12 }}>
          Job ID: <code>{job}</code>
          <div style={{ marginTop: 4, fontSize: 12, opacity: 0.8 }}>
            Consulte o estado em /evaluation/eval-service/jobs/{job}
          </div>
        </div>
      )}
    </div>
  );
}


