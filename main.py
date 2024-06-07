import streamlit as st
import pandas as pd
import numpy as np
from transformers import pipeline

# Load the GPT model
generator = pipeline('text-generation', model='distilgpt2')


def generate_timetable(subjects, marks, days):
    total_marks = sum(marks)
    time_distribution = [(mark / total_marks) for mark in marks]

    schedule = []
    daily_hours = 5  # Maximum of 5 hours per day

    for day in range(1, days + 1):  # Start counting days from 1
        day_schedule = {}
        remaining_hours = daily_hours
        for subject, time in zip(subjects, time_distribution):
            if time == 0:  # If subject has no marks, allocate 0 hours
                day_schedule[subject] = 0
            else:
                study_time = min(time * daily_hours, remaining_hours)  # Limit study time to daily hours and subject time requirement
                study_time = round(study_time, 1)  # Round study time to one decimal place
                day_schedule[subject] = study_time
                remaining_hours -= study_time

        schedule.append(day_schedule)

    return schedule






import re


def enhance_timetable_with_gpt(timetable):
    # Convert timetable to a prompt format for GPT
    print(timetable)
    prompt = "Enhance the following study timetable:\n\n"
    for day, schedule in enumerate(timetable, start=1):
        prompt += f"Day {day}:\n"
        for subject, time in schedule.items():
            prompt += f"  {subject}: {time:.2f} hours\n"
        prompt += "\n"

    # Generate enhanced timetable
    enhanced_timetable = generator(prompt, max_length=500, num_return_sequences=1)[0]['generated_text']

    # Parse the enhanced timetable using regular expressions
    pattern = r"Day \d+:\n(.*?)(?:\n\n|$)"
    matches = re.finditer(pattern, enhanced_timetable, re.DOTALL)

    enhanced_schedule = []
    for match in matches:
        day_schedule_text = match.group(1).strip()
        day_schedule = {}
        for line in day_schedule_text.split('\n'):
            if ':' in line:
                subject, time_str = line.split(':', 1)
                time_str = time_str.strip()  # Remove leading/trailing whitespace
                if time_str:  # Check if time_str is not empty
                    try:
                        time = float(time_str.split()[0])
                        day_schedule[subject.strip()] = time
                    except ValueError:
                        print(f"Invalid time format for line: {line}")
                else:
                    print(f"Empty time string for line: {line}")
        enhanced_schedule.append(day_schedule)

    return enhanced_schedule


# Streamlit UI
st.title("Personalized Study Timetable Generator with GPT")

num_subjects = st.number_input("Enter the number of subjects:", min_value=1, step=1)
subjects = [st.text_input(f"Enter the name of subject {i + 1}:") for i in range(num_subjects)]
marks = [st.number_input(f"Enter the marks for subject {i + 1}:", min_value=0.0, max_value=100.0, step=1.0) for i in
         range(num_subjects)]
study_days = st.number_input("Enter the number of days for study preparation:", min_value=1, step=1, value=7)

if st.button("Generate Timetable"):
    timetable = generate_timetable(subjects, marks, study_days)

    if timetable:
        enhanced_timetable = enhance_timetable_with_gpt(timetable)
        if enhanced_timetable:
            # Create a DataFrame with subjects as rows and study days as columns
            subjects = set()
            study_days = len(enhanced_timetable)
            for day_schedule in enhanced_timetable:
                subjects.update(day_schedule.keys())
            df = pd.DataFrame(index=subjects, columns=[f"Day {i + 1}" for i in range(study_days)])

            # Fill in the DataFrame with study hours for each subject and day
            for day, day_schedule in enumerate(enhanced_timetable):
                for subject, time in day_schedule.items():
                    df.at[subject, f"Day {day + 1}"] = time

            # Fill NaN values with 0 for display purposes
            df = df.fillna(0)

            # Display the transposed DataFrame
            st.write(df.T)
        else:
            st.write("No enhanced timetable generated.")
    else:
        st.write("No timetable generated.")


