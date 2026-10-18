"""Owner/SYSTEM directory DACL using Win32, with exact read-back verification.

No account-name resolution, shell, temporary broad ACL or source-data operation.
API contracts: https://learn.microsoft.com/windows/win32/api/aclapi/
The caller validates the task-owned directory and rejects reparse points first.
"""
import ctypes
from ctypes import wintypes as w


class WindowsAclError(ValueError):
    """Fixed diagnostic code; no path, account identifier or sensitive value."""


def require(value,code):
    if not value:raise WindowsAclError(code)


class WindowsAcl:
    def __init__(self):
        self.a=ctypes.WinDLL('advapi32',use_last_error=True)
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        ptr=ctypes.c_void_p;pp=ctypes.POINTER(ptr)
        self.k.GetCurrentProcess.argtypes=[];self.k.GetCurrentProcess.restype=w.HANDLE
        self.k.CloseHandle.argtypes=[w.HANDLE];self.k.CloseHandle.restype=w.BOOL
        self.k.LocalFree.argtypes=[ptr];self.k.LocalFree.restype=ptr
        self.a.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,ctypes.POINTER(w.HANDLE)];self.a.OpenProcessToken.restype=w.BOOL
        self.a.GetTokenInformation.argtypes=[w.HANDLE,ctypes.c_int,ptr,w.DWORD,ctypes.POINTER(w.DWORD)];self.a.GetTokenInformation.restype=w.BOOL
        self.a.ConvertSidToStringSidW.argtypes=[ptr,ctypes.POINTER(w.LPWSTR)];self.a.ConvertSidToStringSidW.restype=w.BOOL
        self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes=[w.LPCWSTR,w.DWORD,pp,ctypes.POINTER(w.DWORD)]
        self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype=w.BOOL
        self.a.GetSecurityDescriptorDacl.argtypes=[ptr,ctypes.POINTER(w.BOOL),pp,ctypes.POINTER(w.BOOL)]
        self.a.GetSecurityDescriptorDacl.restype=w.BOOL
        self.a.GetSecurityDescriptorControl.argtypes=[ptr,ctypes.POINTER(w.WORD),ctypes.POINTER(w.DWORD)]
        self.a.GetSecurityDescriptorControl.restype=w.BOOL
        self.a.SetNamedSecurityInfoW.argtypes=[w.LPWSTR,ctypes.c_int,w.DWORD,ptr,ptr,ptr,ptr]
        self.a.SetNamedSecurityInfoW.restype=w.DWORD
        self.a.GetNamedSecurityInfoW.argtypes=[w.LPWSTR,ctypes.c_int,w.DWORD,pp,pp,pp,pp,pp]
        self.a.GetNamedSecurityInfoW.restype=w.DWORD
        self.a.GetAce.argtypes=[ptr,w.DWORD,pp];self.a.GetAce.restype=w.BOOL

    def sid_string(self,sid):
        output=w.LPWSTR()
        require(self.a.ConvertSidToStringSidW(sid,ctypes.byref(output)),'SID_STRING')
        try:return output.value
        finally:self.k.LocalFree(ctypes.cast(output,ctypes.c_void_p))

    def current_user(self):
        token=w.HANDLE();size=w.DWORD()
        require(self.a.OpenProcessToken(self.k.GetCurrentProcess(),8,ctypes.byref(token)),'PROCESS_TOKEN')
        try:
            self.a.GetTokenInformation(token,1,None,0,ctypes.byref(size))
            require(size.value>=ctypes.sizeof(ctypes.c_void_p),'TOKEN_SIZE')
            buffer=ctypes.create_string_buffer(size.value)
            require(self.a.GetTokenInformation(token,1,buffer,size,ctypes.byref(size)),'TOKEN_USER')
            # TOKEN_USER begins with SID_AND_ATTRIBUTES; its first member is PSID.
            sid=ctypes.c_void_p.from_buffer(buffer).value
            return self.sid_string(sid)
        finally:self.k.CloseHandle(token)

    def restrict(self,path):
        expected={self.current_user(),'S-1-5-18'}
        sddl='D:P'+''.join('(A;OICI;FA;;;'+sid+')' for sid in sorted(expected))
        descriptor=ctypes.c_void_p()
        require(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,ctypes.byref(descriptor),None),'DACL_PARSE')
        try:
            present=w.BOOL();defaulted=w.BOOL();dacl=ctypes.c_void_p()
            require(self.a.GetSecurityDescriptorDacl(descriptor,ctypes.byref(present),ctypes.byref(dacl),ctypes.byref(defaulted)) and present.value and dacl.value,'DACL_DESCRIPTOR')
            # Replace the DACL in one operation. Never reset to a permissive
            # parent ACL, even transiently; inheritable owner/SYSTEM rights only.
            name=ctypes.create_unicode_buffer(str(path))
            require(self.a.SetNamedSecurityInfoW(name,1,0x80000004,None,None,dacl,None)==0,'DACL_SET')
        finally:self.k.LocalFree(descriptor)
        self.verify(path,expected)

    def verify(self,path,expected):
        descriptor=ctypes.c_void_p();dacl=ctypes.c_void_p();name=ctypes.create_unicode_buffer(str(path))
        require(self.a.GetNamedSecurityInfoW(name,1,4,None,None,ctypes.byref(dacl),None,ctypes.byref(descriptor))==0,'DACL_READ')
        try:
            control=w.WORD();revision=w.DWORD()
            require(self.a.GetSecurityDescriptorControl(descriptor,ctypes.byref(control),ctypes.byref(revision)) and control.value&0x1000,'DACL_PROTECTION')
            require(bool(dacl.value),'DACL_NULL')
            # ACL header: revision, reserved, uint16 size, uint16 ACE count.
            count=ctypes.c_uint16.from_address(dacl.value+4).value
            found=set();require(count==len(expected),'DACL_ACE_COUNT')
            for index in range(count):
                ace=ctypes.c_void_p();require(self.a.GetAce(dacl,index,ctypes.byref(ace)),'DACL_ACE_READ')
                kind=ctypes.c_ubyte.from_address(ace.value).value
                flags=ctypes.c_ubyte.from_address(ace.value+1).value
                mask=ctypes.c_uint32.from_address(ace.value+4).value
                sid=self.sid_string(ace.value+8)
                require(kind==0 and flags==3 and mask==0x1f01ff and sid in expected,'DACL_ACE_SCOPE')
                found.add(sid)
            require(found==expected,'DACL_PRINCIPALS')
        finally:self.k.LocalFree(descriptor)
