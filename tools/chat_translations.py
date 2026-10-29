# Traducoes proprias das frases do historico de NPCs (ChatHistory) que o jogo escreve fixas em ingles no C++
# (UHZCommunityNPCSubSys::Tick/DecayStats) e que nao tem traducao oficial. {X} = nome de NPC ou texto inserido.
# Chave: prefixo da cultura do jogo (2 letras de GetCurrentCulture). Ingles fica como esta.
# As demais falas usam a traducao oficial do jogo (DT_NPC_Responses e DT_TaskConfig) via FindTextInLocalizationTable.
OWN = {
    '{X} has died.': {
        'pt': '{X} morreu.', 'de': '{X} ist gestorben.', 'es': '{X} ha muerto.', 'fr': '{X} est mort.',
        'it': '{X} è morto.', 'ja': '{X}が死亡しました。', 'ko': '{X}이(가) 사망했습니다.', 'ru': '{X} погиб.', 'zh': '{X}死了。'},
    'Taking a short break.': {
        'pt': 'Fazendo uma pausa curta.', 'de': 'Mache eine kurze Pause.', 'es': 'Tomando un breve descanso.',
        'fr': 'Je fais une petite pause.', 'it': 'Faccio una breve pausa.', 'ja': '少し休憩中。', 'ko': '잠깐 쉬는 중.',
        'ru': 'Небольшой перерыв.', 'zh': '稍作休息。'},
    "I can't deal with {X} anymore, I'm leaving the camp!": {
        'pt': 'Não aguento mais {X}, vou sair do acampamento!', 'de': 'Ich halte {X} nicht mehr aus, ich verlasse das Lager!',
        'es': '¡Ya no aguanto a {X}, me voy del campamento!', 'fr': 'Je ne supporte plus {X}, je quitte le camp !',
        'it': 'Non sopporto più {X}, lascio il campo!', 'ja': 'もう{X}には耐えられない、キャンプを出ていく！',
        'ko': '더 이상 {X}을(를) 못 참겠어, 캠프를 떠날 거야!', 'ru': 'Я больше не могу терпеть {X}, я ухожу из лагеря!',
        'zh': '我受不了{X}了，我要离开营地！'},
    'Task failed': {
        'pt': 'A tarefa falhou', 'de': 'Aufgabe fehlgeschlagen', 'es': 'La tarea falló', 'fr': 'La tâche a échoué',
        'it': 'Compito fallito', 'ja': 'タスク失敗', 'ko': '작업 실패', 'ru': 'Задача провалена', 'zh': '任务失败'},
    'Task {X}': {  # "[Tarefa]-[NPC]: Task <fala>"; a fala {X} tambem e traduzida
        'pt': 'Tarefa {X}', 'de': 'Aufgabe {X}', 'es': 'Tarea {X}', 'fr': 'Tâche {X}', 'it': 'Compito {X}',
        'ja': 'タスク {X}', 'ko': '작업 {X}', 'ru': 'Задача {X}', 'zh': '任务 {X}'},
}
# Frases do C++ iguais a uma fala oficial da DT_NPC_Responses exceto por pontuacao: usam a chave oficial.
ALIASES = {"I think you'll find yourself better off elsewhere {X}.": "I think you'll find yourself better off elsewhere {X}"}
NESTED = {'Task {X}'}  # o {X} destes modelos e outra fala, traduzida antes de inserir
