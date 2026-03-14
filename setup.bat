@echo off
echo ============================================
echo    Alpha Mart - Setup Script
echo ============================================
echo.

echo Step 1: Activating virtual environment...
call myVenv\Scripts\activate
if errorlevel 1 (
    echo Creating new virtual environment...
    python -m venv myVenv
    call myVenv\Scripts\activate
)

echo.
echo Step 2: Installing required packages...
pip install django pillow

echo.
echo Step 3: Creating database tables...
python manage.py makemigrations
python manage.py migrate

echo.
echo Step 4: Adding product categories...
python manage.py shell -c "from myApp.models import Category; cats=[('Smartphones','smartphones','fa-mobile-alt'),('Laptops','laptops','fa-laptop'),('Cameras','cameras','fa-camera'),('Lenses','lenses','fa-circle'),('Audio','audio','fa-headphones'),('Tablets','tablets','fa-tablet-alt'),('Smartwatches','smartwatches','fa-clock'),('Gaming','gaming','fa-gamepad')]; [Category.objects.get_or_create(name=n,slug=s,icon=i) for n,s,i in cats]; print('Categories created!')"

echo.
echo Step 5: Creating admin account...
python manage.py createsuperuser

echo.
echo ============================================
echo    SETUP COMPLETE!
echo    Run: python manage.py runserver
echo    Open: http://127.0.0.1:8000/
echo    Admin: http://127.0.0.1:8000/admin/
echo ============================================
pause
