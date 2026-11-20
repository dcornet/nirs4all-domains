// Deliberately exceed a small test Job limit. Successful exit is an adversary failure.
const retained=[];
console.log('ADVERSARY_ALLOCATION_STARTED');
for(let i=0;i<64;i++){retained.push(Buffer.alloc(32*1024*1024,1));console.log('ADVERSARY_STEP',i+1);}
throw new Error('MEMORY_CONTAINMENT_DID_NOT_REFUSE_THE_ADVERSARY');
