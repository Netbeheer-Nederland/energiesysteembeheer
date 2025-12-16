@echo off
pushd ..

if exist _site rd /s /q _site
if exist _build rd /s /q _build

popd
