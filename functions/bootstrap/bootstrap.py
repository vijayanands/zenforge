def ingest_data_into_pinecone_until_now():
    # Get the current date
    current_date = datetime.now()
    # Get the data from the beginning of the year until now
    start_date = current_date.replace(month=1, day=1)
    end_date = current_date
    # Ingest the data
    ingest_data(start_date, end_date)
    return current_date