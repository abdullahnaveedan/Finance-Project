from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from .models import *
import re
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import generate_otp, send_otp_email
import os
import pandas as pd
import numpy as np
from collections import OrderedDict
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
# from django_pandas.io import read_frame


def get_table_data(file_path, dict_to_map):

    try:
        data = pd.read_excel(file_path)
    except Exception as e:
        return f"Error processing the file: {str(e)}"
    data = data.rename(columns = dict_to_map)
    data['disbursement_year'] = data['Disbursement Date'].dt.year
    data['last_payment_year'] = data['Date of Last Payment'].dt.year

          # Group by year and aggregate data
    grouped_by_year = data.groupby('disbursement_year').agg(
        Total_Balance_Capital=('Capital Balance', 'sum'),
        Balance_capital_cases=('Customer Code', 'count')
    ).reset_index()

    grouped_by_year_ultimo_pago = data.groupby('last_payment_year').agg(
      Total_last_payment=('Amount of Last Payment', 'sum'),
      last_payment_cases =('Customer Code', 'count')
    ).reset_index()


          # Grouping 'VALOR_DESEMBOLSOS' by year
    total_disbursement_amount_by_year = data.groupby('disbursement_year')['Disbursement Amount'].sum()


          # Calculating the difference between 'VALOR_DESEMBOLSOS' and 'BALANCE_CAPITAL'

    data['Difference_disbursement_capitalBalance'] = data['Disbursement Amount'] - data['Capital Balance']
    # Grouping this difference by year of 'FECHA_DESEMBOLSO'
    grouped_difference_by_year = data.groupby('disbursement_year')['Difference_disbursement_capitalBalance'].sum().reset_index()

          # Including 'VALOR_DESEMBOLSOS' and 'BALANCE_CAPITAL' in the grouped data
    grouped_data_with_values = data.groupby('disbursement_year').agg(
    Total_disbursement_amount=('Disbursement Amount', 'sum'),
    Total_capital_balance=('Capital Balance', 'sum'),
    total_difference_disbursement_capitalBalance=('Difference_disbursement_capitalBalance', 'sum')
      ).reset_index()

            # Calculating the percentage and cumulative percentage
    grouped_data_with_values['Percentage_Difference'] = (
    grouped_data_with_values['total_difference_disbursement_capitalBalance'] / grouped_data_with_values['Total_disbursement_amount']) * 100
    grouped_data_with_values['Cumulative_Percentage_Difference'] = grouped_data_with_values['Percentage_Difference'].cumsum()
    group = grouped_data_with_values.values.tolist()


    return group
# Create your views here.
@login_required(login_url='sign_in')
def index(request):
    data = file_data.objects.filter(username = request.user).order_by('-id')
    latest_record = data.first()
    file = latest_record.excel_file
    file_path = os.path.join(settings.MEDIA_ROOT, str(file))
    dict_to_map = {'CODIGO_CLIENTE': "Customer Code", 'FECHA_DESEMBOLSO': "Disbursement Date", 'VALOR_DESEMBOLSOS':'Disbursement Amount',
       'VALOR_CUOTA':'Installment Value', 'DIAS_ATRASO_CAPITAL': 'Days of Capital Delay', 'MESES_EN_ATRASO': 'Months in Arrears', 'SALDO_ACTUAL':'Current Balance',
       'BALANCE_CAPITAL': 'Capital Balance', 'INTERES': 'Interest', 'MORA': 'Late Payment Interest / Arrears', 'FECHA_ULTIMO_PAGO': 'Date of Last Payment',
       'MONTO_ULTIMO_PAGO': 'Amount of Last Payment', 'FECHA_CASTIGO': 'Write-Off Date'}

    group = ''
    try:
        data = pd.read_excel(file_path)
        group = get_table_data(file_path, dict_to_map)
    except Exception as e:
        messages.warning(request , "Error processing the file.")
    data = pd.read_excel(file_path)
    data = data.rename(columns = dict_to_map)
    cols_drop=['Customer Code','Disbursement Date','Date of Last Payment','Write-Off Date']
    filtered_data = data.drop(columns=cols_drop)
    mean = filtered_data.mean()
    toMean = mean.to_dict()

    #Total rows in a dataset
    dataset_len = len(data)

    #Total unique rows in a dataset
    unique_customers = data['Customer Code'].nunique()

    # This data is for double bar plot of Write off count and total disbursed count by year
    # Create a new column for the write-off year
    data['write_off_year'] = data['Write-Off Date'].dt.year

    # Calculate write-off count per year
    write_off_count_per_year = data.groupby('write_off_year')['Write-Off Date'].count()
    write_off_index = list(write_off_count_per_year.index)
    write_off_values = list(write_off_count_per_year.values)


    # Calculate yearly loan performance
    data['Year'] = data['Disbursement Date'].dt.year
    yearly_performance = data.groupby('Year').size()
    disbursed_index = list(yearly_performance.index)
    disbursed_values = list(yearly_performance.values)



    # This data is for plot of distribution of Time to Write off
    #Time to Write-Off
    data['Time to Write-Off'] = round((data['Write-Off Date'] - data['Disbursement Date']).dt.days / 365.25)
    time_to_write_off = dict(OrderedDict(sorted(data['Time to Write-Off'].value_counts().to_dict().items())))
    timeToWriteOFF_x = list(time_to_write_off.keys())
    timeToWriteOFF_y = list(time_to_write_off.values())
    # Customer Risk Profile Analysis (Days of Capital Delay)
    #This data is for Distribution of Days of Capital Delay
    days_of_capital_delay = data[['Days of Capital Delay']]
    daysOfCapitalDelay = list(days_of_capital_delay['Days of Capital Delay'])

    # Analysis of Capital Balance over Time
    #This data is for Average Capital Balance Over Time
    data['Year of Last Payment'] = data['Date of Last Payment'].dt.year
    capital_balance_over_time = data.groupby('Year of Last Payment')['Capital Balance'].mean()
    capitalBalanceIndex = list(capital_balance_over_time.index)
    capitalBalanceValues= list(np.round_(capital_balance_over_time.values))


    # Distribution of Months in Arrears
    # This data is for plot of Distribution of Months in Arrears
    months_in_arrears_distribution = dict(OrderedDict(sorted(data['Months in Arrears'].value_counts().to_dict().items())))

    monthInArrearsDistribution_x = list(months_in_arrears_distribution.keys())
    monthInArrearsDistribution_y = list(months_in_arrears_distribution.values())

    # Loan Age (Time since disbursement to the current date or write-off date)
    # This data is for plot of Distribution of Loan Age
    data['Loan Age'] = round((pd.to_datetime('2024-01-01') - data['Disbursement Date']).dt.days / 365.25)
    loan_age_distribution = dict(OrderedDict(sorted(data['Loan Age'].value_counts().to_dict().items())))
    loanAgeDistribution_x = list(loan_age_distribution.keys())
    loanAgeDistribution_y = list(loan_age_distribution.values())
    # This data is for pie plot of Loan Size Category
    #Loan Size Category
    data['Loan Size Category'] = pd.cut(data['Disbursement Amount'], bins=[0, 100000, 500000, 1000000], labels=["Small (0 - 100K)", "Medium (100K - 500K)", "Large (500K - 1M)"])

    # Assuming you have already calculated the proportion_by_loan_size
    proportion_by_loan_size = data['Loan Size Category'].value_counts(normalize=True)
    loanSizeIndex = list(proportion_by_loan_size.index)
    loanSizeValues = list(np.round_(proportion_by_loan_size.values*100 , decimals = 3))

    y_index = sorted(set(disbursed_index) | set(write_off_index))

    # Initialize a-y and b-y with zeros
    disbursed_values_updated = [0] * len(y_index)
    write_off_values_updated = [0] * len(y_index)

    # Update a-y based on the values from disbursed_index and disbursed_values
    for i, x_value in enumerate(disbursed_index):
        index = y_index.index(x_value)
        disbursed_values_updated[index] = disbursed_values[i]

    # Update b-y based on the values from write_off_index and write_off_values
    for i, x_value in enumerate(write_off_index):
        index = y_index.index(x_value)
        write_off_values_updated[index] = write_off_values[i]

    # Read and send excel file

    context = {
             'dataset_mean' : toMean, # Done Speedometer
             'dataset_length':dataset_len, # Done mini-1
             'Unique_customers':unique_customers, # Done mini-2
             'doublebar': {'x': [y_index], 'y': [disbursed_values_updated],'z': [write_off_values_updated]}, # Done Stack bar
             'time_to_write_off': {'x':timeToWriteOFF_x, 'y':timeToWriteOFF_y}, # Line bar
             'lineGraph':{'x':[capitalBalanceIndex],'y':[capitalBalanceValues]}, # Done Line Graph
             'months_in_arrears_distribution':{'x' : monthInArrearsDistribution_x , 'y' : monthInArrearsDistribution_y}, # done Line bar
             'loan_age_distribution':{'x': loanAgeDistribution_x, 'y':loanAgeDistribution_y}, # Done Line bar
             'proportion_by_loan_size': {'x':[loanSizeIndex],'y':[loanSizeValues]} ,# Done PIE
             'group' : group
            }
    return render(request, "dashboard.html",context)

def sign_in(request):
    if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                # Store the user's email in the session
                request.session['email'] = user.email
                user_record = file_data.objects.filter(username = request.user).order_by('-id') 
                
                if len(user_record) > 0:
                    latest_record = user_record.first()
                    file = latest_record.excel_file
                    myfile = checkFile(file)
                    if myfile == True:
                        return redirect("index")
                    else:
                        return redirect("upload-file")
            else:
                messages.warning(request, 'Invalid email or password. Please try again.')

    return render(request, "sign_in.html")

def sign_out(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect("sign_in")


#validate user's data provided by sing_up function
def validate_data(first_name, last_name, username, email, password, confirm_password):
    if password != confirm_password:
        return False, "Passwords do not match."

    if not re.match("^[a-zA-Z0-9]+$", username):
        return False, "Username can only contain alphanumeric characters."

    if User.objects.filter(username=username).exists():
        return False, "Username is already taken. Choose a different one."

    if not re.match("^[a-zA-Z]+$", first_name):
        return False, "First name can only contain alphabet characters."

    if not re.match("^[a-zA-Z]+$", last_name):
        return False, "Last name can only contain alphabet characters."

    if User.objects.filter(email=email).exists():
        return False, "Email is already registered. Choose a different one."

    if not (any(c.isalpha() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~" for c in password) and
            len(password) >= 8):
        return False, "Password must contain at least one alphabet character, one digit, one special character, and be at least 8 characters long."

    return True, "Validation successful."


#performing otp validation by request from otp.html
def otp_validation(request):
    if request.method == "POST":
        if request.method == "POST":
            entered_otp = (
                request.POST.get("otp-1", "") +
                request.POST.get("otp-2", "") +
                request.POST.get("otp-3", "") +
                request.POST.get("otp-4", "")
            )

        # Determine the context (signup or forget password)
        context = request.session.get('otp_context')
        if context == 'sign_up':
            # Retrieve validated user data from the session
            validated_user_data = request.session.get('validated_user_data', None)

            if validated_user_data and entered_otp == validated_user_data['otp']:
                # OTP validation successful, create and save the user
                user = User.objects.create_user(
                    username=validated_user_data['username'],
                    email=validated_user_data['email'],
                    password=validated_user_data['password']
                )
                user.first_name = validated_user_data['first_name']
                user.last_name = validated_user_data['last_name']
                user.save()

                # Authenticate and log in the user
                user = authenticate(request, username=validated_user_data['username'], password=validated_user_data['password'])
                if user is not None:
                    auth_login(request, user)
                    return redirect("upload-file")
            else:
                # Incorrect OTP, redirect to sign_up.html
                messages.warning(request , "Incorrect OTP. Please try again.")
                return render(request, "otp.html")

        elif context == 'forget_password':
            # Retrieve forget password data from the session
            forget_password_data = request.session.get('forget_password')

            if forget_password_data and entered_otp == forget_password_data['otp']:
                # OTP validation successful, proceed with forget password logic
                # (e.g., allow the user to reset their password)
                return render(request, "reset_password.html")
            else:
                # Incorrect OTP, redirect to forget_password.html
                messages.warning(request, "Incorrect OTP. Please try again.")
                return render(request, "otp.html")

        elif context == 'reset_password':
            # Retrieve forget password data from the session
            reset_password_data = request.session.get('reset_password')

            if reset_password_data and entered_otp == reset_password_data['otp']:
                # OTP validation successful, proceed with reset password logic
                # (e.g., allow the user to reset their password)
                return render(request, "reset_password.html")
            else:
                # Incorrect OTP, redirect to forget_password.html
                messages.warning(request, "Incorrect OTP. Please try again.")
                return render(request, "sign_up.html")

    # Redirect to sign_up.html if the request is not POST
    return render(request, "sign_up.html")


def sign_up(request):
    if request.method == "POST":
        getFirstName = request.POST.get("firstname")
        getLastName = request.POST.get("lastname")
        getUserName = request.POST.get("username")
        getEmail = request.POST.get("email")
        getPassword = request.POST.get("password")
        getConfirmPassword = request.POST.get("confirmPassword")

        #calling validation data function
        validation_result, validation_message = validate_data(
            getFirstName, getLastName, getUserName, getEmail, getPassword, getConfirmPassword
        )
        if not validation_result:
            # If validation fails, display an error message
            messages.warning(request, validation_message)
            return render(request, "sign_up.html")

        otp = generate_otp()
        send_otp_email(getEmail, otp)

        request.session['otp_context'] = 'sign_up'
        #Stores the user's data in session
        request.session['validated_user_data'] = {
            'first_name': getFirstName,
            'last_name': getLastName,
            'username': getUserName,
            'email': getEmail,
            'password': getPassword,
            'otp': otp,
            }
        return render(request, "otp.html")
    return render(request, "sign_up.html")


def forget_password(request):
    if request.method == "POST":
        getEmail = request.POST.get("email")
        # Check if the email exists in the database
        try:
            user = User.objects.get(email=getEmail)
        except User.DoesNotExist:
            messages.warning(request, "Email does not exist. Please Enter a valid email.")
            return redirect("forget_password")

        # Generate and send OTP
        otp = generate_otp()
        send_otp_email(getEmail, otp)

        request.session['otp_context'] = 'forget_password'
        print("Session = ", request.session.get('otp_context'))
        request.session['forget_password'] = {
            'email': getEmail,
            'otp': otp,
        }

        return render(request, "otp.html")

    return render(request, "forget_password.html")


def reset_password(request):
    if request.method == "POST":
        # Retrieve email from the session
        getEmail = request.session.get('email')
        getPassword = request.POST.get("password")

        if not getEmail:
            messages.error(request, "Invalid or missing email. Please try again.")
            return render(request, "reset_password.html")

        otp = generate_otp()
        send_otp_email(getEmail, otp)

        request.session['otp_context'] = 'reset_password'
        request.session['reset_password'] = {
            'email': getEmail,
            'password': getPassword,
            'otp': otp,
        }

        return render(request, "otp.html")

    return render(request, "reset_password.html")

def upload_file(request):

    return render(request, "upload_file.html")

def checkFile(file):
    file_path = os.path.join(settings.MEDIA_ROOT, str(file))
    try:
        data = pd.read_excel(file_path) 
        dict_to_map = {
            'CODIGO_CLIENTE': "Customer Code", 
            'FECHA_DESEMBOLSO': "Disbursement Date", 
            'VALOR_DESEMBOLSOS':'Disbursement Amount',
            'VALOR_CUOTA':'Installment Value', 
            'DIAS_ATRASO_CAPITAL': 'Days of Capital Delay', 
            'MESES_EN_ATRASO': 'Months in Arrears', 
            'SALDO_ACTUAL':'Current Balance',
            'BALANCE_CAPITAL': 'Capital Balance', 
            'INTERES': 'Interest', 
            'MORA': 'Late Payment Interest / Arrears', 
            'FECHA_ULTIMO_PAGO': 'Date of Last Payment',
            'MONTO_ULTIMO_PAGO': 'Amount of Last Payment', 
            'FECHA_CASTIGO': 'Write-Off Date'
        }
        spanishFile = set(list(dict_to_map.keys()))
        englishFile = set(list(dict_to_map.values()))
        header = set(list(data.columns.tolist()))

        if header == englishFile or header == spanishFile:
            return True
        else: 
            return False
    except Exception as e:
        return False
    return False

def submit_excel(request):
    if request.method == "POST":
        excel = request.FILES.get("excelFile" , None)
        file_name = ''
        if excel:
                file_name = str(excel)
                file_name = default_storage.save('excel/' + file_name, ContentFile(excel.read()))
                input_excel = file_name
        else:
            input_excel = ''
        file_data(username = request.user, excel_file = input_excel).save()
        data = file_data.objects.filter(username = request.user).order_by('-id')
        latest_record = data.first()
        file = latest_record.excel_file
        myfile = checkFile(file)
        
        if myfile == True:
            # messages.success(request , "Congratulation. Your File is been Processed")
            return redirect("index")
        else:
            messages.warning(request , "Error: The header in your file does not match our requirements.")
            os.remove(os.path.join(settings.MEDIA_ROOT, str(file)))
            latest_record.delete()
            return redirect("upload-file")
    return redirect("upload-file")

def show_sign_in(request):

    return render(request, "sign_in.html")

def show_sign_up(request):

    return render(request, "sign_up.html")

def show_forget_password(request):

    return render(request, "forget_password.html")
