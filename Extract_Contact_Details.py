# Author: Tarek Rahman
import re, lxml.html, time, os, traceback
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def readyDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging", "enable-automation"]
    )
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.maximize_window()
    driver.set_page_load_timeout(40)
    return driver


def crawl(driver, website):
    phoneregEx = r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]"
    domain = re.sub(
        r"^http:\/\/www\.|^https:\/\/www\.|^https:\/\/|^http:\/\/|^www\.|\/$",
        "",
        website,
    )
    driver.get("http://" + domain)
    tree = lxml.html.fromstring(driver.page_source)
    text = " " + tree.text_content().strip().replace("\n", " ").title()
    try:
        phone = parse_phone(driver)
        if not phone:
            phone = driver.execute_script(
                """const matches = (input) => {
				const arr = [...input.matchAll(/[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]/g)]
				return arr
			};
			return matches(document.body.textContent);
			"""
            )
            phone = "\n".join(set([p.strip() for p in phone]))
    except:
        phone = None
    try:
        facebook = tree.xpath('//*[contains(@href,"facebook.com")]/@href')[0]
    except:
        facebook = None
    try:
        linkedin = tree.xpath('//*[contains(@href,"linkedin.com")]/@href')[0]
    except Exception as e:
        linkedin = None
    try:
        twitter = tree.xpath('//*[contains(@href,"twitter.com")]/@href')[0]
    except Exception as e:
        twitter = None
    try:
        instagram = tree.xpath('//*[contains(@href,"instagram.com")]/@href')[0]
    except Exception as e:
        instagram = None
    try:
        email = parse_email(driver)
        if not email:
            email = driver.execute_script(
                """
				const matches = (input) => {
					const arr = [...input.matchAll(/\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+\b/g)]
					return arr
				};
				return matches(document.body.textContent);
			"""
            )
            email = "\n".join(
                set(
                    [
                        e.strip().lower()
                        for e in email
                        if isinstance(
                            re.match(
                                r"\.js$|\.jpg$|\.png$|\.gif$|\.css$|\.\d+$", e.strip()
                            ),
                            re.Match,
                        )
                    ]
                )
            )
    except Exception as e:
        print(e)
        email = None
    return {
        "source_domain": domain,
        "phone": phone,
        "email": email,
        "facebook": facebook,
        "twitter": twitter,
        "instagram": instagram,
        "linkedin": linkedin,
    }


def parse_email(driver):
    try:
        return "\n".join(
            set(
                [
                    el.get_attribute("href").replace("mailto:", "").lower()
                    if not el.get_attribute("href") == "#"
                    else el.text
                    for el in driver.find_elements(
                        By.XPATH, '//*[starts-with(@href,"mailto:")]'
                    )
                ]
            )
        )
    except Exception as e:
        return None


def parse_phone(driver):
    try:
        return "\n".join(
            set(
                [
                    el.get_attribute("href").replace("tel:", "")
                    for el in driver.find_elements(
                        By.XPATH, '//*[starts-with(@href,"tel:")]'
                    )
                ]
            )
        )
    except Exception as e:
        return None


if __name__ == "__main__":
    if not os.path.exists("./websites.csv"):
        print("websites.csv file not found")
        time.sleep(5)
        exit()
    websites = pd.read_csv("websites.csv")
    if not "domains" in list(websites.columns):
        print('your first coluumn header/title should be called "domains"')
        time.sleep(5)
        exit()
    driver = readyDriver()
    output = []
    for index, website in enumerate(websites.domains.to_list()):
        try:
            content = crawl(driver, website)
            output.append(content)
            print(index, output[-1])
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            print(
                f"failed tp scrap contact details from {website}. Skipping to next one"
            )
    pd.DataFrame(output).to_excel("Results_Export.xlsx", index=False)
