# Traducoes proprias dos rotulos da aba Comunidade que o jogo grava como texto "invariante" (nunca traduzido) ou cuja
# chave oficial nao tem traducao. Chave: prefixo da cultura do jogo (2 letras de GetCurrentCulture). Ingles fica como esta.
# Vocabulario alinhado com o do jogo (Comunidade/Gemeinschaft/Сообщество, Tarefa/Aufgabe, nivel de perigo, etc.).
LANGS = ('pt', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'ru', 'zh')
T = {
    # UI_CommunityTab
    'Community Morale': {
        'pt': 'Moral da Comunidade', 'de': 'Gemeinschaftsmoral', 'es': 'Moral de la Comunidad', 'fr': 'Moral de la communauté',
        'it': 'Morale della comunità', 'ja': 'コミュニティの士気', 'ko': '커뮤니티 사기', 'ru': 'Мораль сообщества', 'zh': '社区士气'},
    'Community': {
        'pt': 'Comunidade', 'de': 'Gemeinschaft', 'es': 'Comunidad', 'fr': 'Communauté', 'it': 'Comunità', 'ja': 'コミュニティ',
        'ko': '커뮤니티', 'ru': 'Сообщество', 'zh': '社区'},
    'Build a community base to start a community': {
        'pt': 'Construa uma base comunitária para iniciar uma comunidade',
        'de': 'Baue eine Gemeinschaftsbasis, um eine Gemeinschaft zu gründen',
        'es': 'Construye una base comunitaria para iniciar una comunidad',
        'fr': 'Construisez une base communautaire pour fonder une communauté',
        'it': 'Costruisci una base comunitaria per fondare una comunità',
        'ja': 'コミュニティを始めるにはコミュニティベースを建設してください',
        'ko': '커뮤니티를 시작하려면 커뮤니티 기지를 건설하세요',
        'ru': 'Постройте базу сообщества, чтобы основать сообщество',
        'zh': '建造一个社区基地来建立社区'},
    'Community Stats': {  # titulo de painel estreito (fonte 30): palavra curta, como o "STATS" oficial do jogo em cada idioma
        'pt': 'Estatísticas', 'de': 'Statistiken', 'es': 'Estadísticas', 'fr': 'Statistiques', 'it': 'Statistiche',
        'ja': '統計', 'ko': '통계', 'ru': 'Статистика', 'zh': '统计'},
    'Supply': {
        'pt': 'Suprimentos', 'de': 'Vorräte', 'es': 'Suministros', 'fr': 'Provisions', 'it': 'Provviste', 'ja': '物資',
        'ko': '보급품', 'ru': 'Припасы', 'zh': '物资'},
    # UI_CommunityMemberInfo
    'Current Task:': {
        'pt': 'Tarefa Atual:', 'de': 'Aktuelle Aufgabe:', 'es': 'Tarea actual:', 'fr': 'Tâche actuelle :', 'it': 'Compito attuale:',
        'ja': '現在のタスク：', 'ko': '현재 작업:', 'ru': 'Текущая задача:', 'zh': '当前任务：'},
    'Action History': {
        'pt': 'Histórico de Ações', 'de': 'Aktionsverlauf', 'es': 'Historial de acciones', 'fr': 'Historique des actions',
        'it': 'Cronologia azioni', 'ja': '行動履歴', 'ko': '행동 기록', 'ru': 'История действий', 'zh': '行动记录'},
    'Work-Schedule': {
        'pt': 'Agenda de Trabalho', 'de': 'Arbeitsplan', 'es': 'Horario de trabajo', 'fr': 'Horaires de travail',
        'it': 'Orario di lavoro', 'ja': '作業スケジュール', 'ko': '작업 일정', 'ru': 'График работы', 'zh': '工作安排'},
    'Status': {  # chave oficial E9AF272D existe mas sem pt/de; mesmas palavras do jogo nos outros idiomas
        'pt': 'Status', 'de': 'Status', 'es': 'Estado', 'fr': 'Statut', 'it': 'Stato', 'ja': '状態', 'ko': '상태', 'ru': 'Статус',
        'zh': '状态'},
    'N/A': {
        'pt': 'N/D', 'de': 'k. A.', 'es': 'N/D', 'fr': 'N/D', 'it': 'N/D', 'ja': 'なし', 'ko': '없음', 'ru': 'Н/Д', 'zh': '无'},
    # UI_CommunityMember (linha do membro na lista, ao lado do nome)
    'Morale': {  # mesmas palavras da chave oficial DC2A6A90 (que nao tem italiano)
        'pt': 'Moral', 'de': 'Moral', 'es': 'Moral', 'fr': 'Moral', 'it': 'Morale', 'ja': '士気', 'ko': '사기', 'ru': 'Мораль',
        'zh': '士气'},
    # UI_PreTaskInfo
    'Danger Lv:': {
        'pt': 'Nível de Perigo:', 'de': 'Gefahrenlevel:', 'es': 'Nivel de peligro:', 'fr': 'Niveau de danger :',
        'it': 'Livello di pericolo:', 'ja': '危険度：', 'ko': '위험도:', 'ru': 'Уровень опасности:', 'zh': '危险程度：'},
    'Task:': {
        'pt': 'Tarefa:', 'de': 'Aufgabe:', 'es': 'Tarea:', 'fr': 'Tâche :', 'it': 'Compito:', 'ja': 'タスク：', 'ko': '작업:',
        'ru': 'Задача:', 'zh': '任务：'},
    'Avg Duration': {
        'pt': 'Duração Média', 'de': 'Ø Dauer', 'es': 'Duración media', 'fr': 'Durée moyenne', 'it': 'Durata media',
        'ja': '平均所要時間', 'ko': '평균 소요 시간', 'ru': 'Средняя длительность', 'zh': '平均时长'},
    'Required items:': {
        'pt': 'Itens Necessários:', 'de': 'Benötigte Gegenstände:', 'es': 'Objetos necesarios:', 'fr': 'Objets requis :',
        'it': 'Oggetti richiesti:', 'ja': '必要なアイテム：', 'ko': '필요 아이템:', 'ru': 'Нужные предметы:', 'zh': '所需物品：'},
}
# rotulos fixos do designer (TextBlock variavel -> texto em ingles gravado no widget)
LABELS = {
    'UI_CommunityTab': {'TextBlock_1': 'Community Morale', 'TextBlock_4': 'Community',
                        'TextBlock_6': 'Build a community base to start a community', 'TextBlock_7': 'Community Stats',
                        'TextBlock_8': 'Supply'},
    'UI_CommunityMemberInfo': {'TextBlock_1': 'Current Task:', 'TextBlock_3': 'Action History', 'TextBlock_4': 'Work-Schedule'},
    'UI_CommunityMember': {'TextBlock_2': 'Morale'},
    'UI_PreTaskInfo': {'TextBlock': 'Danger Lv:', 'TextBlock_1': 'Task:', 'TextBlock_4': 'Avg Duration',
                       'TextBlock_6': 'Required items:'},
}
# horarios da agenda (strings fixas no UpdateInfo, variavel local -> texto). Traducao oficial: a chave do Game.locres
# (namespace "") com esse texto exato em ingles e traducao em todos os idiomas e escolhida no build (patch_uitexts.py).
SCHEDULE = {'Temp_string_Variable': 'Once', 'Temp_string_Variable_2': 'Morning', 'Temp_string_Variable_3': 'Afternoon',
            'Temp_string_Variable_4': 'Evening', 'Temp_string_Variable_5': 'Late-Night'}
# limite de largura de cada rotulo traduzido, como multiplo da largura do PROPRIO texto em ingles no mesmo TextBlock (que o
# layout do jogo comporta). No jogo, o texto em ingles e a traducao sao medidos (mesma fonte/tamanho) e, se a traducao passar
# de fator x ingles, a escala dela e reduzida na proporcao. Vale igual para qualquer idioma. Ingles fica como o jogo.
FIT = {
    'UI_CommunityTab': {'TextBlock_7': 1.0,    # titulo das estatisticas: painel estreito, "Supply" logo abaixo (sem 2a linha)
                        'TextBlock_4': 1.15,   # "Community" no canto esquerdo do cabecalho
                        'TextBlock_1': 1.0},   # "Community Morale" no canto direito do cabecalho
    'UI_CommunityMemberInfo': {'TextBlock_1': 2.0, 'TextBlock_3': 3.0, 'TextBlock_4': 1.6},
    'UI_CommunityMember': {'TextBlock_2': 1.2},  # coluna estreita da linha do membro
    'UI_PreTaskInfo': {'TextBlock': 1.8, 'TextBlock_1': 2.5, 'TextBlock_4': 1.8, 'TextBlock_6': 1.6},
}
# rotulos centralizados num espaco de largura limitada e sem nada logo abaixo: quebra automatica de linha (AutoWrapText) +
# texto centralizado, gravados no proprio widget
WRAP = {'UI_CommunityTab': ['TextBlock_6',    # aviso grande (fonte 50) no centro da aba
                            'TextBlock_8']}   # "Supply" (fonte 25), primeiro item da coluna das barras
