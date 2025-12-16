@echo off
pushd ..

call bundle exec jekyll serve -s _build -d _site --livereload --incremental --open-url

popd
