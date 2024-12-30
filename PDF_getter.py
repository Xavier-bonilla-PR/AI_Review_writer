import requests
from bs4 import BeautifulSoup
import re
import os
import logging
import time
from urllib.parse import urljoin, urlparse, unquote
import hashlib
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SciHubPMCCrawler:
    def __init__(self, download_folder="downloads"):
        self.base_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/"
        self.download_folder = download_folder
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0'
        })
        self.timeout = (10, 20)
        self.max_retries = 3
        self.scihub = SciHub()
        
        os.makedirs(self.download_folder, exist_ok=True)

    def get_with_retry(self, url, stream=False):
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, stream=stream)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for URL {url}: {e}")
                if attempt == self.max_retries - 1:
                    logging.error(f"All attempts failed for URL {url}")
                    return None
                time.sleep(2 ** attempt)
        return None

    def get_article_content(self, url):
        logging.info(f"Retrieving article from URL: {url}")
        response = self.get_with_retry(url)
        if response:
            return response.text
        return None

    def extract_references(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        references = []
        for ref_div in soup.find_all('div', class_='ref-cit-blk'):
            ref_text = ref_div.get_text(strip=True)
            ref_links = ref_div.find_all('a', href=True)
            references.append((ref_text, ref_links))
        return references
    
    def check_pubmed_link(self, pubmed_url):
        response = self.get_with_retry(self.fix_url(pubmed_url))
        if response:
            pubmed_soup = BeautifulSoup(response.text, 'html.parser')
            doi_link = pubmed_soup.find('a', {'data-ga-category': 'full-text', 'data-ga-action': 'doi'})
            pdf_link = pubmed_soup.find('a', {'data-ga-category': 'full-text', 'data-ga-action': 'pdf'})
            return self.fix_url(doi_link['href']) if doi_link else None, self.fix_url(pdf_link['href']) if pdf_link else None
        return None, None

    def check_pmc_for_pdf(self, pmc_id):
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
        pmc_content = self.get_article_content(pmc_url)
        if pmc_content:
            pmc_soup = BeautifulSoup(pmc_content, 'html.parser')
            pdf_link = pmc_soup.select_one('.pdf-link a')
            if pdf_link:
                return self.fix_url(pdf_link['href'])
        return None
    
    def check_doi_for_pdf(self, doi_url):
        response = self.get_with_retry(doi_url)
        if response:
            doi_soup = BeautifulSoup(response.text, 'html.parser')
            # Check for Wiley pattern
            wiley_pdf = doi_soup.select_one('a[aria-label="Download PDF"]')
            if wiley_pdf:
                return self.fix_url(wiley_pdf['href'])
            # Check for general PDF link
            pdf_link = doi_soup.find('a', string=re.compile('PDF', re.I))
            if pdf_link:
                return self.fix_url(pdf_link['href'])
        return None
      
    def get_doi_and_pdf(self, ref_links):
        doi = None
        pdf_link = None
        pmc_id = None
        pubmed_url = None
        for link in ref_links:
            href = link['href']
            if 'doi.org' in href and not doi:
                doi = self.fix_url(href)
            elif href.endswith('.pdf') and not pdf_link:
                pdf_link = self.fix_url(href)
            elif 'pubmed.ncbi.nlm.nih.gov' in href and not pubmed_url:
                pubmed_url = href
            elif '/pmc/articles/' in href and not pmc_id:
                pmc_id = href.split('/pmc/articles/')[-1].split('/')[0]

        if pubmed_url and not (doi or pdf_link):
            doi, pdf_link = self.check_pubmed_link(pubmed_url)

        if pmc_id and not pdf_link:
            pdf_link = self.check_pmc_for_pdf(pmc_id)

        if doi and not pdf_link:
            pdf_link = self.check_doi_for_pdf(doi)

        return doi, pdf_link

    def fix_url(self, url):
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return urljoin(self.base_url, url)
        elif not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url

    def download_pdf(self, identifier, filename):
        try:
            result = self.scihub.download(identifier, self.download_folder, filename)
            if 'err' not in result:
                logging.info(f"PDF downloaded: {os.path.join(self.download_folder, filename)}")
                return True
            else:
                logging.error(f"Failed to download PDF: {result['err']}")
        except Exception as e:
            logging.error(f"Error downloading PDF: {str(e)}")
        return False

    def generate_filename(self, pmc_id, ref_number, content):
        pdf_hash = hashlib.md5(content).hexdigest()
        return f"reference_{pmc_id}_{ref_number}-{pdf_hash[-20:]}.pdf"

    def ask_user_for_pdf(self, ref_text, ref_number, doi):
        print(f"\nReference {ref_number}: {ref_text[:100]}...")
        print(f"DOI: {doi}" if doi else "DOI: Not available")
        print("PDF not found automatically. Please provide the file path if you have it saved locally,")
        print("or a direct link to the PDF if available.")
        
        while True:
            local_path = input("Enter local file path (or press Enter to skip): ").strip()
            if not local_path:
                break
            if os.path.isfile(local_path):
                print(f"File found: {local_path}")
                return "local", local_path
            else:
                print(f"File not found: {local_path}")
                retry = input("Would you like to try another path? (y/n): ").strip().lower()
                if retry != 'y':
                    break
        
        url = input("Enter PDF URL (or press Enter to skip): ").strip()
        if url:
            print(f"URL provided: {url}")
            return "url", url
        else:
            print("No URL provided.")
            return None, None
    
    def process_user_provided_pdf(self, source, path_or_url, pmc_id, ref_number):
        try:
            if source == "local":
                print(f"Processing local file: {path_or_url}")
                with open(path_or_url, 'rb') as f:
                    content = f.read()
                print("Local file read successfully.")
            else:  # url
                print(f"Downloading PDF from URL: {path_or_url}")
                response = self.get_with_retry(path_or_url, stream=True)
                if response and response.headers.get('Content-Type') == 'application/pdf':
                    content = response.content
                    print("PDF downloaded successfully.")
                else:
                    print("Failed to download PDF or invalid content type.")
                    return None

            filename = self.generate_filename(pmc_id, ref_number, content)
            filepath = os.path.join(self.download_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(content)
            print(f"PDF saved successfully: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
        return None
    
    def download_user_provided_pdf(self, url, pmc_id, ref_number):
        try:
            response = self.get_with_retry(url, stream=True)
            if response and response.headers.get('Content-Type') == 'application/pdf':
                content = response.content
                filename = self.generate_filename(pmc_id, ref_number, content)
                filepath = os.path.join(self.download_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(content)
                logging.info(f"User-provided PDF downloaded: {filepath}")
                return filepath
            else:
                logging.error("Failed to download user-provided PDF or invalid content type")
        except Exception as e:
            logging.error(f"Error downloading user-provided PDF: {str(e)}")
        return None

    def crawl_references(self, pmc_id):
        url = urljoin(self.base_url, pmc_id)
        html_content = self.get_article_content(url)
        if not html_content:
            return None

        references = self.extract_references(html_content)
        results = []

        for i, (ref_text, ref_links) in enumerate(references, 1):
            logging.info(f"Processing reference {i}/{len(references)}")
            doi, pdf_link = self.get_doi_and_pdf(ref_links)

            result = {'text': ref_text, 'doi': doi}
            identifier = doi or pdf_link
            
            if identifier:
                try:
                    pdf_content = self.scihub.fetch(identifier)
                    if 'pdf' in pdf_content:
                        filename = self.generate_filename(pmc_id, i, pdf_content['pdf'])
                        if self.download_pdf(identifier, filename):
                            result['pdf'] = os.path.join(self.download_folder, filename)
                        else:
                            result['pdf_error'] = f'Failed to download PDF from {identifier}'
                    else:
                        result['pdf_error'] = f'No PDF content found for {identifier}'
                except Exception as e:
                    result['pdf_error'] = f'Error fetching PDF: {str(e)}'
            else:
                result['pdf_error'] = 'No identifier found for PDF'

            if 'pdf' not in result and pdf_link:
                user_pdf_path = self.download_user_provided_pdf(pdf_link, pmc_id, i)
                if user_pdf_path:
                    result['pdf'] = user_pdf_path
                else:
                    result['pdf_error'] = 'Failed to download PDF from direct link'

            if 'pdf' not in result:
                source, path_or_url = self.ask_user_for_pdf(ref_text, i, doi)
                if path_or_url:
                    user_pdf_path = self.process_user_provided_pdf(source, path_or_url, pmc_id, i)
                    if user_pdf_path:
                        result['pdf'] = user_pdf_path
                    else:
                        result['pdf_error'] = 'Failed to process user-provided PDF'
                else:
                    print("No PDF provided by user.")

            results.append(result)
            time.sleep(2)

        return results
    
    def second_pass_for_missing_pdfs(self, results, pmc_id):
        print("\nSecond pass for missing PDFs:")
        for i, result in enumerate(results, 1):
            if 'pdf' not in result:
                print(f"\nStill missing PDF for reference {i}:")
                source, path_or_url = self.ask_user_for_pdf(result['text'], i, result['doi'])
                if path_or_url:
                    user_pdf_path = self.process_user_provided_pdf(source, path_or_url, pmc_id, i)
                    if user_pdf_path:
                        result['pdf'] = user_pdf_path
                        del result['pdf_error']
                    else:
                        result['pdf_error'] = 'Failed to process user-provided PDF in second pass'
                else:
                    print("No PDF provided for this reference in the second pass.")
        return results
    

class SciHub(object):
    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0'}
        self.available_base_url_list = self._get_available_scihub_urls()
        self.base_url = self.available_base_url_list[0] + '/'

    def _get_available_scihub_urls(self):
        urls = []
        res = requests.get('https://sci-hub.now.sh/')
        s = self._get_soup(res.content)
        for a in s.find_all('a', href=True):
            if 'sci-hub.' in a['href']:
                urls.append(a['href'])
        return urls

    def _get_soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    def fetch(self, identifier):
        try:
            url = self._get_direct_url(identifier)
            res = self.sess.get(url, verify=False)

            if res.headers['Content-Type'] != 'application/pdf':
                self._change_base_url()
                raise Exception('Failed to fetch pdf with identifier %s (resolved url %s) due to captcha' % (identifier, url))
            else:
                return {
                    'pdf': res.content,
                    'url': url,
                    'name': self._generate_name(res)
                }

        except requests.exceptions.RequestException as e:
            return {'err': 'Failed to fetch pdf with identifier %s (resolved url %s) due to request exception.' % (identifier, url)}

    def _get_direct_url(self, identifier):
        id_type = self._classify(identifier)
        return identifier if id_type == 'url-direct' else self._search_direct_url(identifier)

    def _search_direct_url(self, identifier):
        res = self.sess.get(self.base_url + identifier, verify=False)
        s = self._get_soup(res.content)
        iframe = s.find('iframe')
        if iframe:
            return iframe.get('src') if not iframe.get('src').startswith('//') else 'http:' + iframe.get('src')

    def _classify(self, identifier):
        if (identifier.startswith('http') or identifier.startswith('https')):
            return 'url-direct' if identifier.endswith('pdf') else 'url-non-direct'
        elif identifier.isdigit():
            return 'pmid'
        else:
            return 'doi'

    def _generate_name(self, res):
        name = res.url.split('/')[-1]
        name = re.sub('#view=(.+)', '', name)
        pdf_hash = hashlib.md5(res.content).hexdigest()
        return '%s-%s' % (pdf_hash, name[-20:])

    def download(self, identifier, destination='', path=None):
        data = self.fetch(identifier)
        
        if 'err' not in data:
            self._save(data['pdf'], os.path.join(destination, path if path else data['name']))
        
        return data

    def _save(self, data, path):
        with open(path, 'wb') as f:
            f.write(data)

    def _change_base_url(self):
        if not self.available_base_url_list:
            raise Exception('Ran out of valid sci-hub urls')
        del self.available_base_url_list[0]
        self.base_url = self.available_base_url_list[0] + '/'
        logging.info(f"Changing to {self.available_base_url_list[0]}")

def main():
    download_folder = "pmc_pdfs"
    crawler = SciHubPMCCrawler(download_folder=download_folder)
    pmc_id = input("Enter the PMC ID to crawl: ").strip()
    results = crawler.crawl_references(pmc_id)

    if results:
        # First pass summary
        print("\nFirst pass summary:")
        for i, ref in enumerate(results, 1):
            print(f"{i}. {ref['text'][:100]}...")
            if ref['doi']:
                print(f"   DOI: {ref['doi']}")
            if 'pdf' in ref:
                print(f"   PDF: {ref['pdf']}")
            elif 'pdf_error' in ref:
                print(f"   PDF Error: {ref['pdf_error']}")

        # Second pass for missing PDFs
        results = crawler.second_pass_for_missing_pdfs(results, pmc_id)

        # Final summary
        print("\nFinal summary after second pass:")
        for i, ref in enumerate(results, 1):
            print(f"{i}. {ref['text'][:100]}...")
            if ref['doi']:
                print(f"   DOI: {ref['doi']}")
            if 'pdf' in ref:
                print(f"   PDF: {ref['pdf']}")
            elif 'pdf_error' in ref:
                print(f"   PDF Error: {ref['pdf_error']}")
    else:
        print("Failed to retrieve or extract data from the article.")

if __name__ == "__main__":
    main()