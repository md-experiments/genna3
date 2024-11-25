import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import uuid

class AsyncAnalyzer:
    def __init__(self, spell_check_endpoint, max_workers=4):
        self.spell_check_endpoint = spell_check_endpoint
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_data = {}
    
    async def _spell_check_text(self, session, text, progress_id, index, total):
        """Async function to check spelling of a single text string"""
        try:
            async with session.post(self.spell_check_endpoint, json={"text": text}) as response:
                result = await response.json()
                self._update_progress(progress_id, index + 1, total)
                return result
        except Exception as e:
            return {"error": str(e), "original_text": text}
    
    def _update_progress(self, progress_id, current, total):
        """Update progress information for a given task"""
        self.progress_data[progress_id] = {
            'current': current,
            'total': total,
            'percentage': (current / total) * 100
        }
    
    async def _process_batch(self, texts, progress_id):
        """Process a batch of texts concurrently with progress tracking"""
        total = len(texts)
        self._update_progress(progress_id, 0, total)
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._spell_check_text(session, text, progress_id, i, total)
                for i, text in enumerate(texts)
            ]
            results = await asyncio.gather(*tasks)
            return results
    
    def process_texts(self, texts, progress_id):
        """Process texts with spell checking in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self._process_batch(texts, progress_id))
            return results
        finally:
            loop.close()
    
    def get_progress(self, progress_id):
        """Get current progress for a given task"""
        return self.progress_data.get(progress_id, {
            'current': 0,
            'total': 0,
            'percentage': 0
        })
    
    def clean_up_progress(self, progress_id):
        """Remove progress data for completed task"""
        self.progress_data.pop(progress_id, None)


class ProgressManager:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, total_items):
        """Create a new task with progress tracking"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'total': total_items,
            'current': 0,
            'percentage': 0,
            'start_time': time.time()
        }
        return task_id
    
    def update_progress(self, task_id, current):
        """Update progress for a task"""
        if task_id in self.tasks:
            total = self.tasks[task_id]['total']
            self.tasks[task_id].update({
                'current': current,
                'percentage': (current / total) * 100 if total > 0 else 0,
                'elapsed_time': time.time() - self.tasks[task_id]['start_time']
            })
    
    def get_progress(self, task_id):
        """Get progress information for a task"""
        return self.tasks.get(task_id)
    
    def clean_up(self, task_id):
        """Remove completed task data"""
        self.tasks.pop(task_id, None)
