import pytest
from unittest.mock import Mock, patch, mock_open
from src import ingest


def test_run_function_basic_flow(mocker):
    """Tests the basic flow of the run function"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock HTML content
    mock_html_content = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/math/test1">Link 1</a>
            <a class="_pkhvgz8" href="/math/test2">Link 2</a>
        </body>
    </html>
    """
    mock_page.content.return_value = mock_html_content

    # Mock open for file writing
    mocker.patch("builtins.open", mock_open())

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Basic verifications
    mock_playwright.chromium.launch.assert_called_once()
    mock_browser.new_page.assert_called()
    mock_page.goto.assert_called()


def test_run_function_with_transcript_links(mocker):
    """Tests the flow with transcript links"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock main HTML content
    main_html = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/math/test1">Link 1</a>
        </body>
    </html>
    """

    # Mock transcript page HTML content
    transcript_html = """
    <html>
        <body>
            <a class="_zl1qagl" href="/transcript1">Transcript 1</a>
            <a class="_zl1qagl" href="/transcript2">Transcript 2</a>
        </body>
    </html>
    """

    # Mock final HTML content with extractable content
    content_html = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/content1">Content 1</a>
        </body>
    </html>
    """

    # Mock HTML content with extractable text
    extractable_html = """
    <html>
        <body>
            <div class="_1fezbb8">This is extractable content</div>
        </body>
    </html>
    """

    # Configure different returns for content() - INCREASE NUMBER OF VALUES
    mock_page.content.side_effect = [
        main_html,      # First call - main page
        transcript_html, # Second call - transcript page
        content_html,    # Third call - content page
        extractable_html, # Fourth call - page with extractable text
        extractable_html, # Fifth call - backup
        extractable_html  # Sixth call - backup
    ]

    # Mock open for file writing
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Verify that file was opened for writing
    mock_file.assert_called()


def test_run_function_with_empty_extracts(mocker):
    """Tests behavior when there's no extractable content"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock HTML content without extractable divs
    mock_html_content = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/math/test1">Link 1</a>
        </body>
    </html>
    """

    # Mock HTML content without extractable text
    empty_html = """
    <html>
        <body>
            <div class="_1fezbb8"></div>
        </body>
    </html>
    """

    mock_page.content.side_effect = [mock_html_content, empty_html, empty_html]

    # Mock open for file writing
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Verify that file was NOT opened (because there's no extractable content)
    mock_file.assert_not_called()


def test_run_function_with_multiple_extracts(mocker):
    """Tests behavior with multiple extracts"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock main HTML content
    main_html = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/math/test1">Link 1</a>
        </body>
    </html>
    """

    # Mock transcript page HTML content
    transcript_html = """
    <html>
        <body>
            <a class="_zl1qagl" href="/transcript1">Transcript 1</a>
        </body>
    </html>
    """

    # Mock final HTML content
    content_html = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/content1">Content 1</a>
        </body>
    </html>
    """

    # Mock HTML content with multiple extracts
    multiple_extracts_html = """
    <html>
        <body>
            <div class="_1fezbb8">First extract</div>
            <div class="_1fezbb8">Second extract</div>
            <div class="_1fezbb8">Third extract</div>
        </body>
    </html>
    """

    mock_page.content.side_effect = [
        main_html,
        transcript_html,
        content_html,
        multiple_extracts_html,
        multiple_extracts_html,
        multiple_extracts_html
    ]

    # Mock open for file writing
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Verify that file was opened for writing
    mock_file.assert_called()


def test_run_function_error_handling(mocker):
    """Tests error handling in the run function"""
    # Mock playwright to raise an exception
    mock_playwright = Mock()
    mock_playwright.chromium.launch.side_effect = Exception("Browser launch failed")

    # Execute the function and expect it to handle the exception gracefully
    try:
        ingest.run(mock_playwright, "https://test.com", "body")
    except Exception as e:
        if "Browser launch failed" in str(e):
            pytest.fail("Function should handle browser launch errors gracefully")


def test_run_function_with_invalid_urls(mocker):
    """Tests behavior with invalid URLs"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock page.goto to raise an exception for invalid URL
    mock_page.goto.side_effect = Exception("Invalid URL")

    # Execute the function and expect it to handle the exception gracefully
    try:
        ingest.run(mock_playwright, "https://invalid-url.com", "body")
    except Exception as e:
        if "Invalid URL" in str(e):
            pytest.fail("Function should handle invalid URL errors gracefully")


def test_run_function_file_writing(mocker):
    """Tests specifically file writing functionality"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock HTML content with extractable text
    extractable_html = """
    <html>
        <body>
            <div class="_1fezbb8">This is extractable content</div>
        </body>
    </html>
    """

    # Mock content to return extractable HTML
    mock_page.content.return_value = extractable_html

    # Mock open for file writing
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)

    # Execute the function
    ingest.run(mock_playwright, "https://www.khanacademy.org/content1", "body")

    # Verify that file was opened with correct name
    mock_file.assert_called_with('test_data/test_content1.txt', 'a')


def test_run_function_with_whitespace_only_content(mocker):
    """Tests behavior with whitespace-only content"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock HTML content with whitespace-only text
    whitespace_html = """
    <html>
        <body>
            <div class="_1fezbb8">   \n\t   </div>
        </body>
    </html>
    """

    mock_page.content.return_value = whitespace_html

    # Mock open for file writing
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Verify that file was NOT opened (whitespace-only content should be ignored)
    mock_file.assert_not_called()


def test_run_function_browser_cleanup(mocker):
    """Tests that browser is properly closed"""
    # Mock playwright
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_page = Mock()

    # Configure playwright mock
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Mock HTML content
    mock_html_content = """
    <html>
        <body>
            <a class="_pkhvgz8" href="/math/test1">Link 1</a>
        </body>
    </html>
    """
    mock_page.content.return_value = mock_html_content

    # Mock open for file writing
    mocker.patch("builtins.open", mock_open())

    # Execute the function
    ingest.run(mock_playwright, "https://test.com", "body")

    # Verify that browser was closed
    mock_browser.close.assert_called_once()
