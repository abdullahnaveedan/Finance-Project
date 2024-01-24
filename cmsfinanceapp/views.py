from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from .models import *
import re
from datetime import datetime
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

def credit_stats(filepath,type):
    try:
        data = pd.read_excel(filepath)
    except Exception as e:
        return f"Error processings the file: {str(e)}"
    
    if type == "Credit":
        data['Issue Date'] = pd.to_datetime(data['Issue Date'], errors='coerce')
        data['Year'] = data['Issue Date'].dt.year  # Extract year from Issue Date
        # Group by the year of Issue Date and calculate yearly sums
        yearly_data = data.groupby('Year').agg(
            Yearly_Sum_Capital_RD=('Capital (RD)', 'sum'),
            Yearly_Sum_Balance_RD=('Balance (RD)', 'sum')
        ).reset_index()
        # Calculate the difference and percentage difference
        yearly_data['Difference'] = yearly_data['Yearly_Sum_Balance_RD'] - yearly_data['Yearly_Sum_Capital_RD']
        yearly_data['Percentage Difference'] = (yearly_data['Difference'] / yearly_data['Yearly_Sum_Capital_RD']) * 100
        # Calculate cumulative percentage difference
        yearly_data['Cumulative Percentage Difference'] = yearly_data['Percentage Difference'].cumsum()
        group = yearly_data.values.tolist()
        return group
    return None
# Create your views here.
@login_required(login_url='sign_in')
def index(request):
    data = file_data.objects.filter(username = request.user).order_by('-id')
    latest_record = data.first()
    file = latest_record.excel_file
    file_path = os.path.join(settings.MEDIA_ROOT, str(file))
    file_type = request.session.get('file_type')
    print("file_type : ", file_type)
    groupofcredit = credit_stats(file_path, file_type)
    group = ''
    try:
        data = pd.read_excel(file_path)
    except Exception as e:
        messages.warning(request ,"Error processing the file.")
        return redirect("upload-file")

    if file_type == "Loan":
        dict_to_map = {'CODIGO_CLIENTE': "Customer Code", 'FECHA_DESEMBOLSO': "Disbursement Date", 'VALOR_DESEMBOLSOS':'Disbursement Amount',
       'VALOR_CUOTA':'Installment Value', 'DIAS_ATRASO_CAPITAL': 'Days of Capital Delay', 'MESES_EN_ATRASO': 'Months in Arrears', 'SALDO_ACTUAL':'Current Balance',
       'BALANCE_CAPITAL': 'Capital Balance', 'INTERES': 'Interest', 'MORA': 'Late Payment Interest / Arrears', 'FECHA_ULTIMO_PAGO': 'Date of Last Payment',
       'MONTO_ULTIMO_PAGO': 'Amount of Last Payment', 'FECHA_CASTIGO': 'Write-Off Date'}
        group = get_table_data(file_path, dict_to_map)
        
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
        data['Recovery rate'] = (data['Capital Balance'] + data['Interest']) / data['Disbursement Amount'] * 100
        recovery_rate = data['Recovery rate'].mean() 
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
                 'group' : group,
                 'recovery_rate' : recovery_rate
                }
    
    elif file_type == "Credit":
        
        cols_drop = ['Product Delinquency', 'Issue Date', 'Expiry Date', 'Next Due Date', 'Capital (US)', 'Minimum Payment (US)',  'Balance (US)', 'Date of last payment',
                    'Late Status', 'NO', 'CasoID', 'Gender', 'Date of Birth', 'Balance',
                    'Amount Paid', 'No. of transactions', 'Number of Vehicles',
                    'Possible Asset', 'Confirmed Phone 1', 'Confirmed Phone 2', 'Seizures']

        filtered_data = data.drop(columns=cols_drop)
        mean = filtered_data.mean()
        toMean = mean.to_dict()
            #length of dataset 
        dataset_length = len(data)
            # No. of unique customers 
        unique_customers = data['CasoID'].nunique()
            # Ths bar chart visualize the frequency distribution of Product delinquency codes
            # Analyzing the 'Product Delinquency' column for unique values and their frequencies
        product_delinquency_insights =  dict(OrderedDict(sorted(data['Product Delinquency'].value_counts().to_dict().items())))
        product_delinquency_insights_x = list(product_delinquency_insights.keys())
        product_delinquency_insights_y = list(product_delinquency_insights.values())
            # This line chart will display the sequence of capital (RD) over time
            # 13. Analysis of Capital Balance over Time
        data['Year of Last Payment'] = data['Date of last payment'].dt.year
        capital_balance_over_time = data.groupby('Year of Last Payment')['Capital (Pesos)'].mean()
        capitalBalanceIndex = list(capital_balance_over_time.index)
        capitalBalanceValues= list(np.round_(capital_balance_over_time.values))
            # This bar graph will tells us the distribution of no. of transactions made
            # Plotting the distribution of 'No. of transactions' with Kernel Density Estimate (KDE)
        bins = [0,50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 750, 1000,np.inf]  # Adjust these ranges as needed
        labels=['0-50', '50-100', '100-150', '150-200', '200-250', '250-300', '300-350', '350-400', '400-450', '450-500', '500-750', '750-1000','>1000']


        # Create a new column in the DataFrame to represent the bins
        data['Transaction Range'] = pd.cut(data['No. of transactions'], bins=bins, labels=labels)

        # Group by the 'Transaction Range' and count occurrences

        transactions_grouped = data['Transaction Range'].value_counts().sort_index()
        transactions_x = transactions_grouped.index.tolist()
        transactions_y = transactions_grouped.values.tolist()
          # The graph visualize the customers who paid before or after the due date 
          # Payment Timeliness (in days)
        data['Payment Timeliness (Months)'] = (data['Next Due Date'] - data['Date of last payment']).dt.days / 30.44
        data = data.dropna(subset=['Payment Timeliness (Months)']) #for dropping NaN values
        # Create a new column for grouping by defining custom ranges
        bins = [0,6, 12, 18,24,32, 38, 60]  # Customize the bins as per your requirements
        labels = ['0-6 months', '6-12 months', '12-18 months', '18-24 months', '24-32 months','32-38 months','38-60 months']
        data['Payment Group'] = pd.cut(data['Payment Timeliness (Months)'], bins=bins, labels=labels, right=False)


        payment_groups = dict(OrderedDict(sorted(data['Payment Group'].value_counts().to_dict().items())))
        payment_timeliness_x = list(payment_groups.keys())
        payment_timeliness_y = list(payment_groups.values())

        # print(payment_timeliness_y)
            # This barchart displays the distribution of account holder's age
            # Current date for age calculation
        current_date = datetime.today()
        # 12. Age of Account Holder
        
        # Convert 'Date of Birth' to datetime
        data['Date of Birth'] = pd.to_datetime(data['Date of Birth'], errors='coerce')

        # Calculate age and convert to integers
        current_date = pd.to_datetime('now' , utc = None)
        data['Age of Account Holder'] = ((current_date - data['Date of Birth']).dt.days / 365.25).astype(int)

        # Count the frequency of each age
        age = dict(OrderedDict(sorted(data['Age of Account Holder'].dropna().value_counts().to_dict().items())))
        age_x = list(age.keys())
        age_y = list(age.values())

       

          # Donut chart displays the distribution of duration of credit cards
          # 1. Recalculate Loan Duration (Years)
        data['Loan Duration (Years)'] = (data['Expiry Date'] - data['Issue Date']).dt.days / 365.25
          # 2. Categorize Loan Duration in Years
        loan_duration_bins = [-1, 2, 5, np.inf]  # Defining bins for loan duration
        loan_duration_labels = ['0-2 years', '2-5 years', '5+ years']
        data['Loan Duration Category'] = pd.cut(data['Loan Duration (Years)'], bins=loan_duration_bins, labels=loan_duration_labels)
          # 3. Prepare data for the donut chart
        loan_duration_category_counts = data['Loan Duration Category'].value_counts()
        loanDurationIndex = list(loan_duration_category_counts.index)
        loanDurationValues = list(np.round_(loan_duration_category_counts.values*100 , decimals = 3))
     
        context = {
                    'dataset_mean' : toMean, # Done
                    'proportion_by_loan_size': {'x':[loanDurationIndex],'y':[loanDurationValues]},# Done Donut
                    'dataset_length':dataset_length, # Done 
                    'Unique_customers':unique_customers, # Done 
                    'months_in_arrears_distribution': {'x':[product_delinquency_insights_x],'y' : [product_delinquency_insights_y]}, # bar Done
                    'lineGraph':{'x':[capitalBalanceIndex],'y':[capitalBalanceValues]}, # D Line Graph
                    'time_to_write_off': {'x':[transactions_x] , 'y':[transactions_y]}, #  Line bar D
                    'loan_age_distribution': {'x' : [payment_timeliness_x] ,'y':[payment_timeliness_y] } , #Line bar D
                    'age': {'x' : [age_x] , 'y' : [age_y]}, # Done Line Bar
                    'group' : groupofcredit # Done
            }
        
    return render(request, "dashboard.html",context)

def sign_in(request):
    if request.method == "POST":
            email = request.POST.get("email")
            password = request.POST.get("password")
            usr = User.objects.get(email = email)
            
            user = authenticate(request, username = usr.username, password=password)

            if user is not None:
                auth_login(request, user)
                request.session['email'] = user.email
                user_record = file_data.objects.filter(username = request.user).order_by('-id') 
                
                if len(user_record) > 0:
                    latest_record = user_record.first()
                    file = latest_record.excel_file
                    myfile = checkFile(file)
                    print(myfile)
                    if myfile == "Loan":
                        request.session['file_type'] = 'Loan'
                        return redirect("index")
                    elif myfile == "Credit":
                        request.session['file_type'] = 'Credit'
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

@login_required(login_url='sign_in')
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

        loan_data = {
            "MORA_PRODUCTO": "Product Delinquency",
            "FECHA_EMISION": "Issue Date",
            "FECHA_VECIMIENTO": "Expiry Date",
            "FECHA_PROX_VENC": "Next Due Date",
            "CAPITAL_RD": "Capital (RD)",
            "CAPITAL_US": "Capital (US)",
            "PAGO_MINIMO_RD": "Minimum Payment (RD)",
            "PAGO_MINIMO_Us": "Minimum Payment (US)",
            "BALANCE_RD": "Balance (RD)",
            "BALANCE_US": "Balance (US)",
            "CAPITAL_EN_PESOS": "Capital (Pesos)",
            "FECHA_ULT_PAGO": "Date of last payment",
            "MONTO_ULT_PAGO": "Amount of last payment",
            "RANGO MORA": "Late Status",
            "NO": "NO",
            "CasoID": "CasoID",
            "Sexo": "Gender",
            "fecha_nacimiento": "Date of Birth",
            "Balance": "Balance",
            "Monto pagado": "Amount Paid",
            "Cantidad de Gestiones": "No. of transactions",
            "Cant. Vehiculos": "Number of Vehicles",
            "Posible bien": "Possible Asset",
            "Telefono confirmado1": "Confirmed Phone 1",
            "Telefono confirmado2": "Confirmed Phone 2",
            "Embargos": "Seizures"
        }

        spanishFile = set(list(dict_to_map.keys()))
        englishFile = set(list(dict_to_map.values()))

        spanishFileCradit = set(list(loan_data.keys()))
        englishFileCradit = set(list(loan_data.values()))

        header = set(list(data.columns.tolist()))
       
        if header == englishFile or header == spanishFile:
            return f"Loan"
        elif  header == englishFileCradit or header ==  spanishFileCradit:
            return f"Credit"
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
        
        if myfile == "Loan":
            request.session['file_type'] = 'Loan'
            return redirect("index")
        elif myfile == "Credit":
            request.session['file_type'] = 'Credit'
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
