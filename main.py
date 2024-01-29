from data_processing import fetch_site_data, find_images

if __name__ == '__main__':
    site_data = fetch_site_data("https://news.usni.org/category/fleet-tracker")
