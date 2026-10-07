@echo off
title THE SRM GRAND - Luxury Hotel & Food Booking Engine
echo ========================================================
echo       THE SRM GRAND - PALACE SUITES & HAUTE CUISINE
echo ========================================================
echo Starting Python Web Server...
echo.
echo Room Database:  excel_data\hotel_bookings.xlsx
echo Food Database:  excel_data\food_orders.xlsx
echo.
echo Opening browser at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000
python app.py
pause
