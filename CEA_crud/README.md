Swagger UI
http://localhost:8000/user/docs  
http://localhost:8000/document/docs 


### Pour un test local 

conda create --name CEA_crud python=3.9
conda activate CEA_crud
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8001 --reload