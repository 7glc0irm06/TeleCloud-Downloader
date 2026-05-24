import sys

def process_file(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('from config import (bot, download_queue', 'from config import (bot')
    if 'from downloader_queue import enqueue' not in content:
        content = content.replace('import os\n', 'import os\nfrom downloader_queue import enqueue\n')
    
    content = content.replace('download_queue.put(', 'enqueue(')
    content = content.replace('download_queue.qsize()', 'len(config.pending_queue)')
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)

process_file(r'c:\Users\Parsa\Desktop\newbot\handlers.py')
process_file(r'c:\Users\Parsa\Desktop\newbot\callbacks.py')
print('Done')
