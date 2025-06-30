import pandas as pd
import requests
import os
import re
from tqdm import tqdm

def download_fch_pdfs(csv_path: str, output_dir: str):
    """
    Downloads FCH (First Course Handout) PDFs from URLs specified in a CSV file.
    PDFs are saved with their corresponding Course ID as the filename.

    Args:
        csv_path (str): The file path to the input CSV containing FCH URLs and Course IDs.
        output_dir (str): The directory where the downloaded PDFs will be saved.
    """
    try:
        timetable = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at '{csv_path}'.")
        return

    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    download_count = 0
    failed_downloads = []

    for index, row in tqdm(timetable.iterrows(), total=timetable.shape[0], desc="Downloading PDFs"):
        fch_url = row.get('FCH URL')
        course_id = row.get('Course ID')

        if pd.isna(fch_url) or not str(fch_url).strip():
            failed_downloads.append({'index': index, 'url': 'N/A', 'reason': 'No FCH URL'})
            continue

        if pd.isna(course_id) or not str(course_id).strip():
            failed_downloads.append({'index': index, 'url': fch_url, 'reason': 'No Course ID'})
            continue

        safe_course_id = re.sub(r'[^\w\s.-]', '', str(course_id)).strip()
        if not safe_course_id:
            failed_downloads.append({'index': index, 'url': fch_url, 'reason': 'Empty Course ID after cleaning'})
            continue

        file_path = os.path.join(output_dir, f"{safe_course_id}.pdf")

        if os.path.exists(file_path):
            download_count += 1
            continue

        try:
            response = requests.get(fch_url, stream=True, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                failed_downloads.append({'index': index, 'url': fch_url, 'reason': f'Not a PDF (Content-Type: {content_type})'})
                continue

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            download_count += 1
        except requests.exceptions.Timeout:
            failed_downloads.append({'index': index, 'url': fch_url, 'reason': 'Request timed out'})
        except requests.exceptions.RequestException as e:
            failed_downloads.append({'index': index, 'url': fch_url, 'reason': str(e)})
        except Exception as e:
            failed_downloads.append({'index': index, 'url': fch_url, 'reason': str(e)})

    print(f"\n--- PDF Download Summary ---")
    print(f"Successfully downloaded {download_count} PDFs (or already existed).")
    if failed_downloads:
        print(f"Failed to download {len(failed_downloads)} PDFs:")
        for failure in failed_downloads:
            course_id_display = timetable.loc[failure['index'], 'Course ID'] if 'index' in failure and failure['index'] < len(timetable) else 'N/A'
            print(f"  - Course ID: {course_id_display}, URL: {failure['url']}, Reason: {failure['reason']}")
    else:
        print("All PDFs processed successfully (downloaded or already present).")

#     download_fch_pdfs(input_csv_file, output_pdf_directory)

#     # Clean up the dummy CSV after execution if it was created for testing
#     if os.path.exists(dummy_csv_path):
#         os.remove(dummy_csv_path)
#         print(f"Cleaned up dummy CSV: {dummy_csv_path}")
