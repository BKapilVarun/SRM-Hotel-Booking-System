@echo off
title Open Hotel & Food Excel Databases
echo Opening hotel_bookings.xlsx and food_orders.xlsx...
if exist "excel_data\hotel_bookings.xlsx" start "" "excel_data\hotel_bookings.xlsx"
if exist "excel_data\food_orders.xlsx" start "" "excel_data\food_orders.xlsx"
echo Done.
pause
