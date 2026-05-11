from pathlib import Path
from urllib.parse import urljoin

from chronologix.configs.court_listener import (
    COURTLISTENER_FILE_STORAGE_URL,
    COURTLISTENER_FILE_OUTPUT_DIR,
    get_courtlistener_headers,
)
from chronologix.utils.RECAP_downloader import download_file, slugify_filename


class CourtListenerRECAPDownloader:
    """
    Downloads available RECAP documents from CourtListener.

    CourtListener-specific responsibility:
    - read filepath_local from RECAP document metadata
    - convert filepath_local into a storage URL
    - call the generic download_file utility
    """

    def __init__(self):
        self.headers = get_courtlistener_headers()

    def download_recap_documents(
        self,
        documents: list[dict],
        output_dir=COURTLISTENER_FILE_OUTPUT_DIR,
    ):
        downloaded_paths = []

        for doc in documents:
            if doc.get("is_available") is not True:
                continue

            filepath_local = doc.get("filepath_local")

            if not filepath_local:
                continue

            document_number = doc.get("document_number") or doc.get("id")
            document_name = doc.get("short_description") or "document"

            filename = f"{document_number}_{slugify_filename(document_name)}"
            file_url = self.build_file_url(filepath_local)

            saved_path = download_file(
                filename=filename,
                url=file_url,
                output_dir=output_dir,
                extension=".pdf",
                headers=self.headers,
            )

            if saved_path:
                downloaded_paths.append(saved_path)

        return downloaded_paths

    @staticmethod
    def build_file_url(filepath_local):
        """
        Convert CourtListener filepath_local into a downloadable storage URL.

        Example:
        recap/gov.uscourts.innd.106288/file.pdf
        ->
        https://storage.courtlistener.com/recap/gov.uscourts.innd.106288/file.pdf
        """
        return urljoin(COURTLISTENER_FILE_STORAGE_URL, filepath_local)
    
    
##----------Uncomment this section for quick test ------------------
# if __name__ == "__main__":
#     from chronologix.sources.court_listener.client import CourtListenerClient
#     from chronologix.sources.court_listener.RECAP_downloader import (
#         CourtListenerRECAPDownloader,
#     )

#     client = CourtListenerClient()
#     docs = client.fetch_recap_documents_for_docket_id(
#         docket_id=59684707,
#         only_available=True,
#     )

#     downloader = CourtListenerRECAPDownloader()
#     downloaded_paths = downloader.download_recap_documents(docs)

#     print(downloaded_paths)