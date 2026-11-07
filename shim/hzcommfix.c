/*
 * hzcommfix.so - HumanitZ NPC Community Dedicated Fix (servidor dedicado Linux)
 *
 * Carregada via LD_PRELOAD. Ao iniciar o processo HumanitZServer-Linux-Shipping, procura na memoria o codigo de
 * UHZCommunityNPCSubSys::ShouldCreateSubsystem (que no servidor dedicado sempre devolve false) e troca 3 bytes para
 * que a funcao devolva o resultado de UWorldSubsystem::ShouldCreateSubsystem, como no host/single-player.
 * Nada e gravado em disco: o executavel continua original e updates do jogo nao desfazem a correcao.
 * Se o padrao nao for encontrado exatamente uma vez (outra versao do jogo), nao altera nada e avisa.
 * As mensagens vao para stdout (console do AMP e de paineis que leem so a saida padrao) e stderr.
 *
 * Protecao do mundo (roda antes do jogo, mesmo com os paks do mod inertes; nao depende de asset nenhum):
 *  1. Trava: se o mod de servidor falta, nao e IoStore ou foi feito para outro build do jogo, o servidor NAO sobe. Um dedicado sem o
 *     mod grava "Extra Recruits" vazia; na volta do mod o jogo sorteia 40 recrutaveis novos e os membros perdem o vinculo (UID).
 *     HZ_SEM_TRAVA=1 no ambiente libera a subida (so avisa).
 *  2. Cofre: Saved/HZ_Cofre/<perfil>_<mundo>: copia da lista e das comunidades + ultimas copias inteiras saudaveis do mundo.
 *  3. Reparo: lista ausente volta do cofre; membro sem vinculo volta pelo cofre ou, sem cofre, pelo PortraitID -> classe BP_Recruit_NPC_<Nome>.
 *     O save original fica em Saved/HZ_Cofre/.../antes_reparo_<data>. Qualquer duvida no formato: nao altera nada.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <dirent.h>
#include <time.h>
#include <fcntl.h>

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


/* ---- arquivos ---- */
#define COPIAS 6
static unsigned char *ler(const char *p, size_t *n) {
    FILE *f = fopen(p, "rb"); if (!f) return NULL;
    struct stat st; if (fstat(fileno(f), &st) != 0 || st.st_size <= 0) { fclose(f); return NULL; }
    unsigned char *d = malloc((size_t)st.st_size + 1);
    if (d && fread(d, 1, (size_t)st.st_size, f) != (size_t)st.st_size) { free(d); d = NULL; }
    fclose(f); if (d) *n = (size_t)st.st_size; return d;
}
static int grava(const char *p, const unsigned char *d, size_t n) {   /* tmp + rename: nunca deixa arquivo pela metade */
    char t[1200]; snprintf(t, sizeof(t), "%s.hz_tmp", p);
    FILE *f = fopen(t, "wb"); if (!f) return 0;
    int ok = fwrite(d, 1, n, f) == n; ok = (fflush(f) == 0) && ok; fsync(fileno(f)); fclose(f);
    if (!ok || rename(t, p) != 0) { unlink(t); return 0; }
    return 1;
}
static int copia(const char *de, const char *para) {
    size_t n; unsigned char *d = ler(de, &n); if (!d) return 0;
    int r = grava(para, d, n); free(d); return r;
}
static int existe(const char *p) { struct stat st; return stat(p, &st) == 0; }
static void msg(const char *fmt, const char *a, const char *b) { char m[1500]; snprintf(m, sizeof(m), fmt, a, b); say(m); }

static uint64_t fnv(const unsigned char *d, size_t n) {
    uint64_t h = 14695981039346656037ULL;
    for (size_t i = 0; i < n; i++) { h ^= d[i]; h *= 1099511628211ULL; }
    return h;
}

/* ---- trava ---- */
static int falha_trava(const char *fmt, const char *a) {
    char t[700], m[900]; snprintf(t, sizeof(t), fmt, a); snprintf(m, sizeof(m), "[hzcommfix] *** TRAVA DE PROTECAO: %s\n", t); say(m);
    if (getenv("HZ_SEM_TRAVA")) { say("[hzcommfix] HZ_SEM_TRAVA definido: subindo mesmo assim, o mundo pode perder os vinculos dos NPCs\n"); return 0; }
    say("[hzcommfix] Servidor NAO iniciado para nao gravar o mundo sem o mod. Atualize o mod para este build do jogo.\n");
    return 1;
}
static int trava(const char *hz) {
    char paks[800], base[900], p[1000]; size_t n;
    snprintf(paks, sizeof(paks), "%s/Content/Paks", hz);
    snprintf(base, sizeof(base), "%s/HumanitZServer-LinuxServer.utoc", paks);
    if (!existe(base)) return 0;                     /* jogo sem IoStore: nada a conferir aqui */
    unsigned char *d = ler(base, &n); if (!d) return 0;
    uint64_t h = fnv(d, n); free(d);
    snprintf(p, sizeof(p), "%s/NPCCommunityFix_Server_P.utoc", paks);
    if (!existe(p) && falha_trava("mod de servidor ausente (NPCCommunityFix_Server_P .pak/.ucas/.utoc)", "")) return 1;
    DIR *dir = opendir(paks); if (!dir) return 0;
    struct dirent *e; int ruim = 0;
    while (!ruim && (e = readdir(dir))) {
        size_t l = strlen(e->d_name);
        if (l < 5 || strcmp(e->d_name + l - 4, ".pak") != 0 || strncmp(e->d_name, "HumanitZServer-", 15) == 0) continue;
        char st[300]; snprintf(st, sizeof(st), "%.*s", (int)l - 4, e->d_name);
        snprintf(p, sizeof(p), "%s/%s.utoc", paks, st);
        if (!existe(p)) { ruim = falha_trava("pak sem .utoc/.ucas sera ignorado pelo jogo: %s", e->d_name); continue; }
        snprintf(p, sizeof(p), "%s/%s.sig", paks, st);
        size_t ns; unsigned char *g = ler(p, &ns);
        if (g) {
            char hex[32]; snprintf(hex, sizeof(hex), "%016llx", (unsigned long long)h);
            if (ns < 16 || memcmp(g, hex, 16) != 0) ruim = falha_trava("mod feito para outro build do jogo: %s", st);
            free(g);
        }
    }
    closedir(dir); return ruim;
}

/* ---- save (GVAS) ---- */
static unsigned char *achar(unsigned char *d, size_t n, const void *pat, size_t l, size_t de) {
    return de >= n ? NULL : memmem(d + de, n - de, pat, l);
}
/* propriedade de nivel raiz: devolve inicio/fim ou 0 */
static int prop(unsigned char *d, size_t n, const char *nome, const char *tipo, size_t *ini, size_t *fim) {
    unsigned char h[80]; size_t ln = strlen(nome) + 1, lt = strlen(tipo) + 1, q = 0;
    uint32_t v = (uint32_t)ln; memcpy(h, &v, 4); memcpy(h + 4, nome, ln); q = 4 + ln;
    v = (uint32_t)lt; memcpy(h + q, &v, 4); memcpy(h + q + 4, tipo, lt); q += 4 + lt;
    unsigned char *a = achar(d, n, h, q, 0); if (!a) return 0;
    size_t p = (size_t)(a - d) + q; int64_t sz; if (p + 8 > n) return 0;
    memcpy(&sz, d + p, 8); p += 8; if (sz < 0) return 0;
    int k = strcmp(tipo, "MapProperty") == 0 ? 2 : 1;       /* Array: tipo interno; Map: chave e valor */
    for (int i = 0; i < k; i++) { uint32_t l2; if (p + 4 > n) return 0; memcpy(&l2, d + p, 4); p += 4 + l2; }
    p += 1; if (p + (size_t)sz > n) return 0;
    *ini = (size_t)(a - d); *fim = p + (size_t)sz; return 1;
}
#define MAXN 200
typedef struct { unsigned char uid[16]; char nome[64]; } Membro;
typedef struct { unsigned char *uid; char nome[64]; } Entrada;
static const unsigned char G_[] = "Guid";
static unsigned char *guid_apos(unsigned char *d, size_t n, size_t de) {
    unsigned char *g = achar(d, n, G_, 5, de); return g ? g + 5 + 17 : NULL;
}
static int entradas(unsigned char *d, size_t ini, size_t fim, Entrada *e) {
    static const char P[] = "BP_Recruit_NPC_"; size_t q = ini; int c = 0;
    while (c < MAXN) {
        unsigned char *a = achar(d, fim, P, 15, q); if (!a) break;
        size_t p = (size_t)(a - d); unsigned char *b = a + 15; int i = 0;
        while (b < d + fim && *b != '.' && i < 63) e[c].nome[i++] = (char)*b++;
        e[c].nome[i] = 0;
        unsigned char *u = achar(d, fim, "UID_19_", 7, p); if (!u) break;
        unsigned char *g = guid_apos(d, fim, (size_t)(u - d)); if (!g) break;
        e[c++].uid = g; q = (size_t)(g - d);
    }
    return c;
}
/* membros com comunidade: mesma leitura de tools/check_vinculo.py */
static int membros(unsigned char *d, size_t ini, size_t fim, Membro *m) {
    static const unsigned char P[] = "\x05\0\0\0Name\0\x0d\0\0\0NameProperty\0"; size_t q = ini; int c = 0;
    static const unsigned char Z[16] = {0};
    while (c < MAXN) {
        unsigned char *a = achar(d, fim, P, sizeof(P) - 1, q); if (!a) break;
        size_t p = (size_t)(a - d); q = p + 10;
        unsigned char *c1 = achar(d, fim, "CommunityUID", 13, p);
        unsigned char *u1 = achar(d, fim, "\x04\0\0\0UID", 8, p);
        unsigned char *r1 = achar(d, fim, "PortraitID", 11, p);
        if (!c1 || !u1 || !r1) break;
        unsigned char *gu = guid_apos(d, fim, (size_t)(u1 - d)), *gc = guid_apos(d, fim, (size_t)(c1 - d));
        if (!gu || !gc || gc + 16 > d + fim || memcmp(gc, Z, 16) == 0) continue;
        unsigned char *t = achar(d, fim, "NameProperty", 13, (size_t)(r1 - d)); if (!t) continue;
        size_t v = (size_t)(t - d) + 13 + 9; uint32_t l; memcpy(&l, d + v, 4);
        if (l == 0 || l > 63) continue;
        memcpy(m[c].uid, gu, 16); memcpy(m[c].nome, d + v + 4, l); m[c].nome[l - 1] = 0; c++;
    }
    return c;
}
static int tem_uid(Entrada *e, int ne, const unsigned char *u) {
    for (int i = 0; i < ne; i++) if (memcmp(e[i].uid, u, 16) == 0) return 1;
    return 0;
}
/* insere ou troca a propriedade inteira; o fim do arquivo e o None da raiz + 4 zeros */
static unsigned char *emenda(unsigned char *d, size_t *n, size_t ini, size_t fim, const unsigned char *b, size_t nb) {
    unsigned char *o = malloc(*n - (fim - ini) + nb + 1); if (!o) return NULL;
    memcpy(o, d, ini); memcpy(o + ini, b, nb); memcpy(o + ini + nb, d + fim, *n - fim);
    *n = *n - (fim - ini) + nb; return o;
}
static int fim_raiz(unsigned char *d, size_t n, size_t *q) {
    static const unsigned char F[] = "\x05\0\0\0None\0\0\0\0\0";
    if (n < 13 || memcmp(d + n - 13, F, 13) != 0) return 0;
    *q = n - 13; return 1;
}

/* copia a pasta do mundo e o <mundo>_HZX para snap; mantem as COPIAS mais novas */
static void guarda_mundo(const char *dirw, const char *nome, const char *cof, const char *sg, const char *sub) {
    char sn[1100], a[1400], b[1400]; snprintf(sn, sizeof(sn), "%s/%s", cof, sub); mkdir(sn, 0755);
    snprintf(a, sizeof(a), "%s/Save_%s.sav", dirw, nome); snprintf(b, sizeof(b), "%s/Save_%s.sav", sn, nome); copia(a, b);
    DIR *w = opendir(dirw); struct dirent *e;
    if (w) { while ((e = readdir(w))) if (strchr(e->d_name, '@')) { snprintf(a, sizeof(a), "%s/%s", dirw, e->d_name); snprintf(b, sizeof(b), "%s/%s", sn, e->d_name); copia(a, b); } closedir(w); }
    snprintf(a, sizeof(a), "%s/%s_HZX.sav", sg, nome); snprintf(b, sizeof(b), "%s/%s_HZX.sav", sn, nome); copia(a, b);
}
static int cmp_nome(const void *a, const void *b) { return strcmp(*(char *const *)a, *(char *const *)b); }
static void gira(const char *cof) {
    DIR *c = opendir(cof); if (!c) return; char *lst[256]; int k = 0; struct dirent *e;
    while ((e = readdir(c)) && k < 256) if (strncmp(e->d_name, "copia_", 6) == 0) lst[k++] = strdup(e->d_name);
    closedir(c); qsort(lst, (size_t)k, sizeof(char *), cmp_nome);
    for (int i = 0; i < k; i++) {
        if (i < k - COPIAS) {
            char p[1400], q[1500]; snprintf(p, sizeof(p), "%s/%s", cof, lst[i]);
            DIR *s = opendir(p);
            if (s) { while ((e = readdir(s))) if (e->d_name[0] != '.') { snprintf(q, sizeof(q), "%s/%s", p, e->d_name); unlink(q); } closedir(s); }
            rmdir(p);
        }
        free(lst[i]);
    }
}
static void mundo(const char *dirw, const char *perfil, const char *nome, const char *sg, const char *hz) {
    char f[1000], cof[1000], er[1100], cm[1100], ts[32], sub[80];
    static Entrada e[MAXN], ec[MAXN]; static Membro m[MAXN];
    snprintf(f, sizeof(f), "%s/Save_%s.sav", dirw, nome);
    snprintf(cof, sizeof(cof), "%s/Saved/HZ_Cofre", hz); mkdir(cof, 0755);
    snprintf(cof, sizeof(cof), "%s/Saved/HZ_Cofre/%s_%s", hz, perfil, nome); mkdir(cof, 0755);
    snprintf(er, sizeof(er), "%s/recrutaveis.bin", cof); snprintf(cm, sizeof(cm), "%s/comunidades.bin", cof);
    time_t t = time(NULL); strftime(ts, sizeof(ts), "%Y%m%d_%H%M%S", localtime(&t));
    size_t n; unsigned char *d = ler(f, &n); if (!d) return;
    size_t i1 = 0, f1 = 0, i2 = 0, f2 = 0, nb = 0, nc = 0, q;
    int tem_er = prop(d, n, "Extra Recruits", "ArrayProperty", &i1, &f1), tem_cm = prop(d, n, "NPCCommunityData", "MapProperty", &i2, &f2);
    unsigned char *b = ler(er, &nb), *c = ler(cm, &nc), *novo = NULL; int mudou = 0;
    size_t nov = n;
    if (!fim_raiz(d, n, &q)) { msg("[hzcommfix] %s: formato inesperado, nada alterado\n", nome, ""); goto fim; }
    if (!tem_er && b) {                       /* servidor rodou sem o mod */
        snprintf(sub, sizeof(sub), "antes_reparo_%s", ts); guarda_mundo(dirw, nome, cof, sg, sub);
        novo = emenda(d, &nov, q, q, b, nb); if (!novo) goto fim;
        free(d); d = novo; n = nov; mudou = 1; msg("[hzcommfix] %s: lista de recrutaveis restaurada do cofre\n", nome, "");
        if (!tem_cm && c && fim_raiz(d, n, &q)) {
            nov = n; novo = emenda(d, &nov, q, q, c, nc);
            if (novo) { free(d); d = novo; n = nov; msg("[hzcommfix] %s: comunidades restauradas do cofre\n", nome, ""); }
        }
        tem_er = prop(d, n, "Extra Recruits", "ArrayProperty", &i1, &f1); tem_cm = prop(d, n, "NPCCommunityData", "MapProperty", &i2, &f2);
    }
    if (tem_er && tem_cm) {
        int ne = entradas(d, i1, f1, e), nm = membros(d, i2, f2, m), faltam = 0;
        for (int i = 0; i < nm; i++) faltam += !tem_uid(e, ne, m[i].uid);
        if (faltam && b) {                    /* lista sorteada de novo: a do cofre conhece os membros? */
            unsigned char *bb = malloc(nb + 1); memcpy(bb, b, nb);
            int nec = entradas(bb, 0, nb, ec), ok = 1;
            for (int i = 0; i < nm; i++) ok &= tem_uid(ec, nec, m[i].uid);
            if (ok) {
                if (!mudou) { snprintf(sub, sizeof(sub), "antes_reparo_%s", ts); guarda_mundo(dirw, nome, cof, sg, sub); }
                nov = n; novo = emenda(d, &nov, i1, f1, b, nb);
                if (novo) {
                    free(d); d = novo; n = nov; mudou = 1; faltam = 0;
                    msg("[hzcommfix] %s: lista de recrutaveis trocada pela do cofre (vinculos dos membros)\n", nome, "");
                    prop(d, n, "Extra Recruits", "ArrayProperty", &i1, &f1); prop(d, n, "NPCCommunityData", "MapProperty", &i2, &f2);
                    ne = entradas(d, i1, f1, e);
                }
            }
            free(bb);
        }
        if (faltam) {                         /* sem cofre: mesma classe, mesmo UID do membro (mesmo tamanho, no lugar) */
            if (!mudou) { snprintf(sub, sizeof(sub), "antes_reparo_%s", ts); guarda_mundo(dirw, nome, cof, sg, sub); }
            for (int i = 0; i < nm; i++) {
                if (tem_uid(e, ne, m[i].uid)) continue;
                for (int k = 0; k < ne; k++) if (strcmp(e[k].nome, m[i].nome) == 0) {
                    memcpy(e[k].uid, m[i].uid, 16); mudou = 1; faltam--;
                    msg("[hzcommfix] %s: %s religado pelo nome\n", nome, m[i].nome); break;
                }
            }
            if (faltam > 0) msg("[hzcommfix] %s: ainda ha membro sem vinculo, ver Saved/HZ_Cofre\n", nome, "");
        }
        if (mudou && !grava(f, d, n)) { msg("[hzcommfix] %s: falha ao gravar o reparo, nada alterado\n", nome, ""); goto fim; }
        if (faltam <= 0) {                    /* saudavel: cofre e copia */
            grava(er, d + i1, f1 - i1); grava(cm, d + i2, f2 - i2);
            snprintf(sub, sizeof(sub), "copia_%s", ts); guarda_mundo(dirw, nome, cof, sg, sub); gira(cof);
        }
    } else if (tem_er) {
        if (mudou) grava(f, d, n);
        grava(er, d + i1, f1 - i1);
    }
fim:
    free(d); free(b); free(c);
}
static void protege(const char *hz) {
    char raiz[900], sg[900], p[1000], w[1400]; 
    snprintf(sg, sizeof(sg), "%s/Saved/SaveGames", hz); snprintf(raiz, sizeof(raiz), "%s/SaveList", sg);
    DIR *a = opendir(raiz); if (!a) return; struct dirent *x, *y;
    while ((x = readdir(a))) {
        if (x->d_name[0] == '.') continue;
        snprintf(p, sizeof(p), "%s/%s", raiz, x->d_name);
        DIR *b = opendir(p); if (!b) continue;
        while ((y = readdir(b))) {
            if (y->d_name[0] == '.') continue;
            snprintf(w, sizeof(w), "%s/%s/Save_%s.sav", p, y->d_name, y->d_name);
            if (existe(w)) { snprintf(w, sizeof(w), "%s/%s", p, y->d_name); mundo(w, x->d_name, y->d_name, sg, hz); }
        }
        closedir(b);
    }
    closedir(a);
}

/* Membro sem tarefa: UHZCommunityNPCSubSys::Tick consulta DT_TaskConfig com a linha None a cada quadro e o log recebe ~120 avisos por segundo.
 * So desliga o aviso (bWarnIfRowMissing) nas chamadas com o contexto "NPC Action DT": o retorno nulo continua igual. mov ecx,1 -> mov ecx,0, mesmo tamanho. */
static void silencia(const char *exe) {
    static const char txt[] = "NPC Action DT";
    unsigned char w[2 * sizeof(txt)];
    for (size_t i = 0; i < sizeof(txt); i++) { w[2 * i] = (unsigned char)txt[i]; w[2 * i + 1] = 0; }
    struct { unsigned char *lo, *hi; int x; } seg[32]; int ns = 0;
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return;
    char line[1024];
    while (fgets(line, sizeof(line), maps) && ns < 32) {
        unsigned long lo, hi; char perms[8], path[600] = "";
        if (sscanf(line, "%lx-%lx %7s %*s %*s %*s %599s", &lo, &hi, perms, path) < 3) continue;
        if (perms[0] != 'r' || strcmp(path, exe) != 0) continue;
        seg[ns].lo = (unsigned char *)lo; seg[ns].hi = (unsigned char *)hi; seg[ns].x = perms[2] == 'x'; ns++;
    }
    fclose(maps);
    uintptr_t alvo = 0;
    for (int i = 0; i < ns && !alvo; i++)
        for (unsigned char *p = seg[i].lo; p + sizeof(w) <= seg[i].hi; p += 2)
            if (*p == 'N' && memcmp(p, w, sizeof(w)) == 0) { alvo = (uintptr_t)p; break; }
    if (!alvo || alvo > 0xffffffffUL) { say("[hzcommfix] aviso de tarefa: texto nao encontrado, nada alterado\n"); return; }
    unsigned char pat[10] = {0xBA, 0, 0, 0, 0, 0xB9, 1, 0, 0, 0};
    unsigned int v = (unsigned int)alvo; memcpy(pat + 1, &v, 4);
    long pg = sysconf(_SC_PAGESIZE); int feitos = 0;
    for (int i = 0; i < ns; i++) {
        if (!seg[i].x) continue;
        for (unsigned char *p = seg[i].lo; p + sizeof(pat) <= seg[i].hi; p++) {
            if (*p != 0xBA || memcmp(p, pat, sizeof(pat)) != 0) continue;
            uintptr_t a = (uintptr_t)(p + 6) & ~(uintptr_t)(pg - 1);
            if (mprotect((void *)a, (size_t)pg, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) continue;
            p[6] = 0;
            mprotect((void *)a, (size_t)pg, PROT_READ | PROT_EXEC);
            feitos++;
        }
    }
    char m[120]; snprintf(m, sizeof(m), "[hzcommfix] aviso de tarefa sem linha silenciado em %d pontos\n", feitos); say(m);
}

__attribute__((constructor)) static void hzcommfix_init(void) {
    char exe[512];
    ssize_t n = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (n <= 0) return;
    exe[n] = 0;
    if (!strstr(exe, "HumanitZServer-Linux-Shipping")) return; /* LD_PRELOAD tambem chega ao shell de inicializacao */
    {   /* <raiz>/HumanitZServer/Binaries/Linux/<exe> -> <raiz>/HumanitZServer */
        char hz[600]; snprintf(hz, sizeof(hz), "%s", exe);
        char *c = strstr(hz, "/Binaries/Linux/");
        if (c) { *c = 0; if (trava(hz)) _exit(1); protege(hz); }
    }
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
    silencia(exe);
}
