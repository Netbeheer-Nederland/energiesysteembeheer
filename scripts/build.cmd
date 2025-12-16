@echo off
pushd ..

robocopy docs _build /e /nfl /ndl

python generate.py _build

popd
