import struct, sys, datetime
d = open(sys.argv[1], 'rb').read()
magic, flags, pe_off, _, sec_off, nhdr = struct.unpack('>4sIIIII', d[:24])
print('magic', magic, 'flags %08x' % flags, 'pe_data_offset 0x%x' % pe_off, 'sec_info 0x%x' % sec_off, 'opt headers', nhdr)
names = {0x2ff:'RESOURCE?',0x3ff:'BASEFILE_FORMAT',0x405:'BASE_REFERENCE',0x5ff:'DELTA_PATCH',0x80ff:'BOUNDING_PATH',0x10001:'ORIGINAL_BASE_ADDRESS',0x10100:'ENTRY_POINT',0x10201:'IMAGE_BASE_ADDRESS',0x103ff:'IMPORT_LIBRARIES',0x18002:'CHECKSUM_TIMESTAMP',0x18102:'ENABLED_FOR_CALLCAP',0x183ff:'ORIGINAL_PE_NAME',0x200ff:'STATIC_LIBRARIES',0x20104:'TLS_INFO',0x20200:'DEFAULT_STACK_SIZE',0x20301:'DEFAULT_FILESYSTEM_CACHE_SIZE',0x20401:'DEFAULT_HEAP_SIZE',0x28002:'PAGE_HEAP_SIZE_AND_FLAGS',0x30000:'SYSTEM_FLAGS',0x40006:'EXECUTION_INFO',0x40201:'TITLE_WORKSPACE_SIZE',0x40310:'GAME_RATINGS',0x40404:'LAN_KEY',0x400ff:'INCLUDE_DESTINATIONS',0x4ff:'?',0xe10402:'XBOX360_LOGO',0xe104ff:'MULTIDISC_MEDIA_IDS',0xe10302:'ALTERNATE_TITLE_IDS',0xe10001:'ADDITIONAL_TITLE_MEMORY',0xe20005:'EXPORTS_BY_NAME'}
hdrs = {}
for i in range(nhdr):
    k, v = struct.unpack('>II', d[24+i*8:32+i*8]); hdrs[k] = v
    print('  %06x %-30s 0x%x' % (k, names.get(k,'?'), v))
def blk(k):
    o = hdrs[k]; n = struct.unpack('>I', d[o:o+4])[0]; return d[o:o+n]
if 0x183ff in hdrs: print('PE name:', blk(0x183ff)[4:].split(b'\0')[0].decode())
if 0x10100 in hdrs: print('entry 0x%x' % hdrs[0x10100])
if 0x10201 in hdrs: print('image base 0x%x' % hdrs[0x10201])
if 0x40006 in hdrs:
    o=hdrs[0x40006]; mid,ver,bver,tid=struct.unpack('>IIII',d[o:o+16]); print('media %08x title %08x version %08x base %08x'%(mid,tid,ver,bver))
if 0x3ff in hdrs:
    b = blk(0x3ff); enc, comp = struct.unpack('>HH', b[4:8]); print('encryption', enc, '(1=AES)', 'compression', comp, '(1=basic 2=LZX)')
    if comp == 2: print('  LZX window 0x%x' % struct.unpack('>I', b[8:12]))
if 0x18002 in hdrs:
    o=hdrs[0x18002]; ck,ts=struct.unpack('>II',d[o:o+8]); print('PE timestamp', datetime.datetime.utcfromtimestamp(ts))
if 0x200ff in hdrs:
    b=blk(0x200ff)[4:]
    for j in range(len(b)//16):
        n=b[j*16:j*16+8].split(b'\0')[0].decode(); a,bb,c,e=struct.unpack('>HHHH',b[j*16+8:j*16+16]); print('  lib %-10s %d.%d.%d.%d'%(n,a,bb,c,e&0xff))
if 0x103ff in hdrs:
    b=blk(0x103ff); strsz,cnt=struct.unpack('>II',b[4:12]); print('import libs:', [s.decode() for s in b[12:12+strsz].split(b'\0') if s])
so=sec_off; img_size=struct.unpack('>I',d[so+4:so+8])[0]; print('image size 0x%x' % img_size)
lo=so+0x110; load_addr=struct.unpack('>I',d[lo:lo+4])[0]
