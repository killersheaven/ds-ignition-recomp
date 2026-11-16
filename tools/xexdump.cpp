#include <xex.h>
#include <image.h>
#include <cstdio>
#include <vector>
int main(int c, char** v){
  FILE* f=fopen(v[1],"rb"); std::vector<uint8_t> d; fseek(f,0,SEEK_END); d.resize(ftell(f)); fseek(f,0,SEEK_SET); fread(d.data(),1,d.size(),f); fclose(f);
  Image img = Xex2LoadImage(d.data(), d.size());
  printf("base 0x%zx size 0x%x entry 0x%zx\n", img.base, img.size, img.entry_point);
  for (auto& s : img.sections) printf("  %-10s 0x%08zx size 0x%08x flags %x\n", s.name.c_str(), s.base, s.size, s.flags);
  FILE* o=fopen(v[2],"wb"); fwrite(img.data.get(),1,img.size,o); fclose(o);
}
