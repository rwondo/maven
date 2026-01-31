@echo off
REM Batch script for MAVEN development on Windows
REM Usage: make.bat <command>

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="test" goto test
if "%1"=="test-cov" goto test-cov
if "%1"=="lint" goto lint
if "%1"=="lint-fix" goto lint-fix
if "%1"=="format" goto format
if "%1"=="format-check" goto format-check
if "%1"=="check" goto check
if "%1"=="clean" goto clean
if "%1"=="build" goto build
if "%1"=="test-together" goto test-together
if "%1"=="example-basic" goto example-basic
if "%1"=="example-together" goto example-together

echo Unknown command: %1
echo Run "make.bat help" for available commands
exit /b 1

:help
echo MAVEN Development Commands (Windows)
echo.
echo   make.bat install          - Install package in development mode
echo   make.bat test             - Run all tests
echo   make.bat test-cov         - Run tests with coverage
echo   make.bat lint             - Run linters
echo   make.bat lint-fix         - Run linters and auto-fix
echo   make.bat format           - Format code with black
echo   make.bat format-check     - Check code formatting
echo   make.bat check            - Run all checks
echo   make.bat clean            - Clean build artifacts
echo   make.bat build            - Build distribution packages
echo   make.bat test-together    - Test Together AI integration
echo   make.bat example-basic    - Run basic example
echo   make.bat example-together - Run Together AI example
exit /b 0

:install
echo Installing MAVEN in development mode...
pip install -e ".[dev]"
exit /b 0

:test
echo Running tests...
pytest tests/ -v
exit /b 0

:test-cov
echo Running tests with coverage...
pytest tests/ -v --cov=maven --cov-report=html --cov-report=term
exit /b 0

:lint
echo Running linters...
ruff check src/ tests/ examples/
mypy src/
exit /b 0

:lint-fix
echo Running linters with auto-fix...
ruff check --fix src/ tests/ examples/
exit /b 0

:format
echo Formatting code...
black src/ tests/ examples/
exit /b 0

:format-check
echo Checking code formatting...
black --check src/ tests/ examples/
exit /b 0

:check
echo Running all checks...
call :format-check
call :lint
call :test
exit /b 0

:clean
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.egg-info rmdir /s /q *.egg-info
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .mypy_cache rmdir /s /q .mypy_cache
if exist .ruff_cache rmdir /s /q .ruff_cache
if exist htmlcov rmdir /s /q htmlcov
if exist .coverage del .coverage
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
echo Clean complete
exit /b 0

:build
echo Building distribution packages...
python -m build
exit /b 0

:test-together
echo Testing Together AI integration...
python test_together.py
exit /b 0

:example-basic
echo Running basic example...
python examples/basic_consensus.py
exit /b 0

:example-together
echo Running Together AI example...
python examples/together_ai_example.py
exit /b 0
