// No workload starts before the parent assigns this process to its memory job.
import {pathToFileURL} from 'node:url';
const admitted=await new Promise(resolve=>process.stdin.once('data',data=>resolve(data.toString())));
if(admitted!=='ADMITTED\n')throw new Error('PRINT_PROCESS_ADMISSION_REQUIRED');
process.argv.splice(1,1);
await import(pathToFileURL(process.argv[1]).href);
