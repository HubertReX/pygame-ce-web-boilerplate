@ECHO OFF
REM generate pydantic model and save schema to:
REM project\config_model\config_schema.json

pushd
cd project\config_model

python config_pydantic.py

popd
