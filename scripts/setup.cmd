@echo off
pushd ..

python -c "" || (
    echo [ERROR] Python is not installed or not in your PATH. Install Python or the portable WinPython.
    exit /b 1
)

ruby -e "" >nul 2>&1 || (
    echo [ERROR] Ruby is not installed. Install Ruby+Devkit.
    exit /b 1
)

call bundle -v >nul 2>&1 || (
    echo [WARNING] Bundler not found. Installing...
    call gem install bundler
)

python -m pip install -r requirements.txt

python -m spacy download nl_core_news_sm

call bundle install

popd
