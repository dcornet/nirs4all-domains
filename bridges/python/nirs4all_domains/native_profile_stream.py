"""Serial JSON-line transport to the unchanged native X characterization API."""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading


class NativeProfileStream:
    def __init__(self,binary,library):
        self.binary=Path(binary).resolve();self.library=Path(library).resolve();self.responses=queue.Queue();self.lock=threading.Lock()
        self.process=subprocess.Popen([str(self.binary),'x-profile-stream','--methods-library',str(self.library)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        def read():
            try:
                for line in self.process.stdout:self.responses.put(line)
            finally:self.responses.put(None)
        self.reader=threading.Thread(target=read,daemon=True);self.reader.start()

    def request(self,payload):
        with self.lock:
            try:
                self.process.stdin.write(json.dumps(payload,allow_nan=False,separators=(',',':'))+'\n');self.process.stdin.flush()
            except (BrokenPipeError,OSError) as error:raise RuntimeError('NATIVE_STREAM_WRITE_FAILED') from error
            try:line=self.responses.get(timeout=600)
            except queue.Empty as error:
                self.process.kill();raise RuntimeError('NATIVE_STREAM_REQUEST_TIMEOUT') from error
            if line is None:raise RuntimeError('NATIVE_STREAM_ENDED_BEFORE_RESPONSE')
            if len(line)>64000000:raise RuntimeError('NATIVE_STREAM_RESPONSE_BYTE_BOUND')
            result=json.loads(line)
            if result['status']!='computed':raise RuntimeError(result['reason'])
            if result['reason'] is not None or result['value'] is None:raise RuntimeError('INVALID_NATIVE_STREAM_RESULT_STATE')
            return result['value']

    def profile(self,spectral,representation,binary=None,library=None,design=None):
        if binary is not None and Path(binary).resolve()!=self.binary:raise ValueError('STREAM_BINARY_SCOPE_CHANGED')
        if library is not None and Path(library).resolve()!=self.library:raise ValueError('STREAM_PROVIDER_SCOPE_CHANGED')
        value=self.request({'spectral':spectral,'representation':representation,'query_ids':design['ids'] if design else [],'include_neighbors':design is not None})
        if value['protocol_version']!='domains.unsupervised.v0.1' or value['test_target_accessed']:raise ValueError('STREAM_X_ONLY_PROTOCOL_VIOLATION')
        if value['n_observations']!=len(spectral['observation_ids']):raise ValueError('STREAM_SOURCE_POPULATION_CHANGED')
        return value

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:self.process.stdin.close()
        try:self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=10)
        self.reader.join(timeout=2)
        self.process.stdout.close();self.process.stderr.close()

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
