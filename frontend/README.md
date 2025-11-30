Terminal 1 :
cd frontend
npm install
npm run dev

In powershell :
docker run -d --name redis-hms -p 6379:6379 redis:7-alpine
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


To run scheduled taks:
celery -A celery_worker.celery call generate_and_send_monthly_reports
celery_worker.celery call send_daily_appointment_reminders