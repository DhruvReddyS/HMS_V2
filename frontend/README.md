Terminal 1 :
cd frontend
npm install
npm run dev

In powershell :
docker ps -a
docker start redis-hms
docker ps

Terminal 2 :
cd backend
celery -A celery_worker.celery worker --loglevel=info --pool=solo

Terminal 3 :
cd backend
celery -A celery_worker.celery beat --loglevel=info

Terminal 4 :
cd backend
python app.py
