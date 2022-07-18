import click
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

@click.command()
@click.option('--url', type=click.STRING, prompt='Google review URL to scrape', help='Google review URL to scrape')
@click.option('--output_csv', type=click.STRING, prompt='Name for output CSV file', help='Name for output CSV file')
def cli(url, output_csv):

    # Set sleep time
    WAIT_TIME = 10

    # Set driver and retrieve url
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(WAIT_TIME)

    '''
    Source for some of the code below:
    https://www.linkedin.com/pulse/webscrape-google-map-reviews-using-selenium-python-choy-siew-wearn/?trk=pulse-article_more-articles_related-content-card
    Some improvements made (ie. disregard owner responses)
    '''

    print('Scrolling to bottom of reviews...')
    last_height = driver.execute_script("return document.body.scrollHeight")
    number = 0
    while True:
        number += 1

        # Scroll to bottom of reviews
        ele = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]')
        driver.execute_script('arguments[0].scrollBy(0, 5000);', ele)
        time.sleep(WAIT_TIME) # Wait to load page; otherwise all reviews might not load

        # Calculate new scroll height and compare with last scroll height
        ele = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]')
        new_height = driver.execute_script("return arguments[0].scrollHeight", ele)
        if number == 5:
            break
        if new_height == last_height:
            break
        last_height = new_height

    # Get reviews and metadata
    driver.implicitly_wait(WAIT_TIME)  # Wait for up to 10sec
    review = driver.find_elements(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[9]')[0]
    print('Parsing information from reviews...')

    # Click "more" for all reviews with longer entries
    buttons = review.find_elements(By.TAG_NAME, 'button')
    for button in buttons:
        if button.text == 'More':
            button.click()
    time.sleep(WAIT_TIME)

    # Parse information from all reviews and add to data frame
    author_list = [author.text for author in review.find_elements(By.CLASS_NAME, "d4r55")]
    stars_list = [stars.get_attribute("aria-label") for stars in review.find_elements(By.CLASS_NAME, "kvMYJc")]
    review_text_list = [review_text.text for review_text in review.find_elements(By.CSS_SELECTOR, "span.wiI7pd")]
    time_since_review_list = [time_since_review.text for time_since_review in review.find_elements(By.CLASS_NAME, "rsqaWe")]

    df = pd.DataFrame({
        'author': author_list,
        'rating': stars_list,
        'review_text': review_text_list,
        'time_since_review': time_since_review_list
    }).replace(r'\n', ' ', regex=True)  # Remove '\n' from reviews

    # Remove file type from name if included
    if '.csv' in output_csv:
        output_csv = output_csv.split('.csv')[0]

    # Output CSV file
    print(f'Outputting information to {output_csv}.csv...')
    output_dir = os.getcwd()
    df.to_csv(f'{output_dir}/{output_csv}.csv', index=False)


if __name__ == "__main__":
   cli()