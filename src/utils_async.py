import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import uuid
from typing import Callable, List, Dict, Any

class AsyncFunction:
    def __init__(self, max_workers: int = None):
        """
        Initialize AsyncFunction with a spell checking function.
        
        Args:
            analyzer_function: Function that takes a textt and returns a dictionary
            max_workers: Number of processes for parallel processing
        """
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.progress_data = {}
        
    def _update_progress(self, progress_id: str, current: int, total: int) -> None:
        """Update progress information for a given task"""
        self.progress_data[progress_id] = {
            'current': current,
            'total': total,
            'percentage': (current / total) * 100,
            'last_update': time.time()
        }

    async def _process_texts_batch(self, texts: List[str], analyzer_function: Callable[[Dict[str, Any]], Dict[str, Any]], start_idx: int, 
                                    progress_id: str, total: int) -> List[Dict]:
        """Process a batch of texts using the spell checker function"""
        loop = asyncio.get_event_loop()
        results = []
        
        for i, text in enumerate(texts, start=start_idx):
            # Run spell check function in process pool to avoid blocking
            result = await loop.run_in_executor(
                self.process_pool,
                analyzer_function,
                text
            )
            results.append(result)
            self._update_progress(progress_id, i + 1, total)
            
        return results

    async def _process_texts(self, texts: List[str], analyzer_function: Callable[[Dict[str, Any]], Dict[str, Any]],
                           progress_id: str, batch_size: int = 10) -> List[Dict]:
        """
        Process all texts in batches to avoid overwhelming the system.
        
        Args:
            texts: List of texts to spell check
            progress_id: ID for tracking progress
            batch_size: Number of texts to process in parallel
        """
        total = len(texts)
        self._update_progress(progress_id, 0, total)
        
        results = []
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await self._process_texts_batch(
                batch, analyzer_function, i, progress_id, total
            )
            results.extend(batch_results)
            
        return results

    def process_texts(self, texts: List[str], analyzer_function: Callable[[Dict[str, Any]], Dict[str, Any]], progress_id: str, 
                     batch_size: int = 10) -> List[Dict]:
        """
        Main entry point for processing texts.
        
        Args:
            texts: List of texts to spell check
            progress_id: ID for tracking progress
            batch_size: Number of texts to process in parallel
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                self._process_texts(texts, analyzer_function, progress_id, batch_size)
            )
            return results
        finally:
            loop.close()

    def get_progress(self, progress_id: str) -> Dict:
        """Get current progress for a given task"""
        return self.progress_data.get(progress_id, {
            'current': 0,
            'total': 0,
            'percentage': 0
        })

    def clean_up_progress(self, progress_id: str) -> None:
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
