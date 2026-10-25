/*
 * hzcommfix.so - HumanitZ NPC Community Dedicated Fix (servidor dedicado Linux)
 *
 * Carregada via LD_PRELOAD. Ao iniciar o processo HumanitZServer-Linux-Shipping, procura na memoria o codigo de
 * UHZCommunityNPCSubSys::ShouldCreateSubsystem (que no servidor dedicado sempre devolve false) e troca 3 bytes para
 * que a funcao devolva o resultado de UWorldSubsystem::ShouldCreateSubsystem, como no host/single-player.
 * Nada e gravado em disco: o executavel continua original e updates do jogo nao desfazem a correcao.
 * Se o padrao nao for encontrado exatamente uma vez (outra versao do jogo), nao altera nada e avisa.
 * As mensagens vao para stdout (console do AMP e de paineis que leem so a saida padrao) e stderr.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>

/* 53 48 89 F3 E8 ?? ?? ?? ?? 48 85 DB 74 09 84 C0 74 05 E8 ?? ?? ?? ?? 31 C0 5B C3 */
static const int PAT[] = {0x53, 0x48, 0x89, 0xF3, 0xE8, -1, -1, -1, -1, 0x48, 0x85, 0xDB, 0x74, 0x09, 0x84, 0xC0,
                          0x74, 0x05, 0xE8, -1, -1, -1, -1, 0x31, 0xC0, 0x5B, 0xC3};
#define PATLEN (int)(sizeof(PAT) / sizeof(PAT[0]))
#define PATCH_OFF 9
static const unsigned char NEWB[] = {0x5B, 0xC3, 0x90}; /* pop rbx; ret; nop */

static void say(const char *msg) {
    fputs(msg, stdout); fflush(stdout);
    fputs(msg, stderr);
}

static int match(const unsigned char *p) {
    for (int i = 0; i < PATLEN; i++)
        if (PAT[i] >= 0 && p[i] != (unsigned char)PAT[i]) return 0;
    return 1;
}

__attribute__((constructor)) static void hzcommfix_init(void) {
    char exe[512];
    ssize_t n = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (n <= 0) return;
    exe[n] = 0;
    if (!strstr(exe, "HumanitZServer-Linux-Shipping")) return; /* LD_PRELOAD tambem chega ao shell de inicializacao */
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return;
    char line[1024];
    unsigned char *found = NULL; int count = 0;
    while (fgets(line, sizeof(line), maps)) {
        unsigned long lo, hi; char perms[8], path[600] = "";
        if (sscanf(line, "%lx-%lx %7s %*s %*s %*s %599s", &lo, &hi, perms, path) < 3) continue;
        if (perms[2] != 'x' || strcmp(path, exe) != 0) continue;
        for (unsigned char *p = (unsigned char *)lo; p + PATLEN <= (unsigned char *)hi; p++)
            if (*p == 0x53 && match(p)) { found = p; count++; }
    }
    fclose(maps);
    if (count != 1) {
        /* ja corrigido em disco (patcher) tambem cai aqui: o padrao original nao existe mais */
        char m[200];
        snprintf(m, sizeof(m), "[hzcommfix] padrao encontrado %d vezes: nada alterado (versao do jogo diferente ou executavel ja corrigido)\n", count);
        say(m);
        return;
    }
    long pg = sysconf(_SC_PAGESIZE);
    uintptr_t a = (uintptr_t)(found + PATCH_OFF) & ~(uintptr_t)(pg - 1);
    if (mprotect((void *)a, (size_t)pg * 2, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) {
        say("[hzcommfix] mprotect falhou: nada alterado\n"); return;
    }
    memcpy(found + PATCH_OFF, NEWB, sizeof(NEWB));
    mprotect((void *)a, (size_t)pg * 2, PROT_READ | PROT_EXEC);
    __builtin___clear_cache((char *)found, (char *)found + PATLEN);
    say("[hzcommfix] subsistema de comunidade habilitado no servidor dedicado\n");
}
