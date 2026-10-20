"""Run with python -m desktop.app. Hardware access starts only on Connect."""
import copy
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
# Ubuntu/Zorin may omit this small optional XCB library. The installer obtains
# the distro package and extracts it locally, without apt install/root.
if sys.platform.startswith('linux'):
    import ctypes
    for library in (Path(__file__).resolve().parents[1]/'.tools/qt-runtime/usr/lib').glob('*/libxcb-cursor.so.0'):
        ctypes.CDLL(str(library),mode=ctypes.RTLD_GLOBAL)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPointF, QRectF, QStandardPaths, QLockFile, QUrl
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QDesktopServices, QCloseEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QTabWidget, QLineEdit, QFileDialog, QMessageBox,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QSplitter, QScrollArea)
from . import config, game, music, firmware
from . import manual
from .runtime import external
from . import __version__
from .engine import Engine, ports

ROOT = Path(__file__).resolve().parents[1]
COLORS = ('#50d890', '#ff666f', '#f5d45d', '#58a6ff', '#ffae54', '#b8c4d6', '#b8c4d6', '#b8c4d6', '#b8c4d6')

class Signals(QObject):
    done = Signal(str, object, object)
    progress = Signal(str)

class Guitar(QWidget):
    selected = Signal(int)
    def __init__(self):
        super().__init__()
        self.setMinimumSize(440, 530)
        self.setAccessibleName('Guitarra visual. Clique numa seta para identificar ou remapear o botão.')
        self.mask, self.pins, self.active = 0, list(config.DEFAULT_PINS), 0
        self.hitboxes = []

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = min(self.width()/470, self.height()/570)
        p.translate((self.width()-470*scale)/2, (self.height()-570*scale)/2)
        p.scale(scale, scale)
        p.fillRect(QRectF(0,0,470,570), QColor('#111925'))
        p.setPen(QPen(QColor('#718096'), 2))
        p.setBrush(QColor('#384355'))
        body = QPainterPath()
        body.moveTo(145,245);body.cubicTo(85,280,58,330,93,370)
        body.cubicTo(33,433,70,530,162,531);body.cubicTo(248,530,269,468,227,415)
        body.cubicTo(216,389,256,334,213,294);body.lineTo(187,330)
        body.lineTo(181,245);body.closeSubpath()
        p.drawPath(body)
        p.setBrush(QColor('#243044'));p.drawRoundedRect(QRectF(140,40,43,299),7,7)
        head = QPainterPath();head.moveTo(138,41);head.lineTo(133,12);head.lineTo(183,5);head.lineTo(189,41);head.closeSubpath()
        p.drawPath(head)
        p.setPen(QPen(QColor('#53657b'),1))
        for x in range(147,180,6):p.drawLine(x,42,x,485)
        for y in range(65,251,35):p.drawLine(140,y,183,y)
        positions = [(161,82),(161,117),(161,152),(161,187),(161,222),
                     (163,353),(163,387),(119,455),(202,481)]
        label_y = [82,117,152,187,222,353,387,455,496]
        self.hitboxes = []
        p.setFont(QFont('Sans',10))
        for i,((x,y),ly) in enumerate(zip(positions,label_y)):
            on=bool(self.mask & config.BITS[i]); color=QColor(COLORS[i])
            p.setPen(QPen(color,3 if i==self.active else 1.4))
            p.setBrush(color if on else QColor('#192232'))
            if i<5:p.drawRoundedRect(QRectF(x-14,y-11,28,22),5,5)
            else:p.drawEllipse(QPointF(x,y),9,9)
            p.drawLine(QPointF(x+17,y),QPointF(282,ly));p.drawLine(282,ly,293,ly)
            p.drawLine(288,ly-4,293,ly);p.drawLine(288,ly+4,293,ly)
            rect=QRectF(300,ly-15,162,30)
            p.setBrush(QColor('#233047') if i==self.active else QColor('#172130'))
            p.drawRoundedRect(rect,5,5)
            p.setPen(QColor('#f4f7fb'))
            p.drawText(rect.adjusted(8,0,-4,0),Qt.AlignmentFlag.AlignVCenter,
                       config.LABELS[i].replace(' / Star Power','')+f' · D{self.pins[i]}')
            self.hitboxes.append((rect, i))
        p.setPen(QColor('#8999ae'));p.setFont(QFont('Sans',9))
        p.drawText(QRectF(20,540,435,25),Qt.AlignmentFlag.AlignCenter,'Clique numa seta para selecionar a função.')
        p.end()

    def mousePressEvent(self, event):
        scale=min(self.width()/470,self.height()/570)
        point=QPointF((event.position().x()-(self.width()-470*scale)/2)/scale,
                      (event.position().y()-(self.height()-570*scale)/2)/scale)
        for rect,index in self.hitboxes:
            if rect.contains(point):
                self.active=index;self.selected.emit(index);self.update();break

class Window(QMainWindow):
    def __init__(self, auto=True):
        super().__init__()
        self.profile=config.load()
        if sys.platform=='win32' and not (config.data_dir()/'profile.json').exists():
            folder=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))/'Clone Hero'
            self.profile.update(game_data=str(folder),songs=str(folder/'Songs'))
        if not self.profile['game']:self.profile['game']=game.discover_game()
        self.engine=Engine(self.profile)
        self.pool=ThreadPoolExecutor(max_workers=2)
        self.signals=Signals();self.signals.done.connect(self.task_done);self.signals.progress.connect(self.message)
        self.callbacks={};self.busy=set();self.selected=0;self.learning=None;self.edge=0;self.rows=[];self.page=1
        self.revision=0
        self.setWindowTitle('Guitar Lab '+__version__);self.resize(1160,820)
        help_action=self.menuBar().addMenu('Ajuda').addAction('Manual do aplicativo')
        help_action.setShortcut('F1');help_action.triggered.connect(self.open_manual)
        base=QWidget();layout=QVBoxLayout(base);layout.setContentsMargins(24,18,24,14);layout.setSpacing(14)
        heading=QHBoxLayout();title=QLabel('GUITAR LAB');title.setStyleSheet('font-size:24px;font-weight:700;color:#67e8a4')
        heading.addWidget(title);heading.addStretch();self.status=QLabel('Desconectado');heading.addWidget(self.status);layout.addLayout(heading)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        self.build_guitar();self.build_setup();self.build_music();self.build_logs()
        self.notice=QLabel('Conecte a guitarra por USB. Mantenha os botões soltos na conexão.');self.notice.setWordWrap(True);layout.addWidget(self.notice)
        self.setCentralWidget(base)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(80)
        self.scan_ports()
        if auto and self.profile.get('auto_connect'):QTimer.singleShot(200,self.connect_device)

    def button(self,text,callback):
        b=QPushButton(text);b.clicked.connect(callback);return b

    def message(self,text):self.notice.setText(str(text))

    def fail(self,exc):
        self.message(str(exc));QMessageBox.warning(self,'Guitar Lab',str(exc))

    def task(self,key,fn,done=None):
        if key in self.busy:return
        self.busy.add(key);self.callbacks[key]=done
        future=self.pool.submit(fn)
        def finished(f):
            try:result,error=f.result(),None
            except Exception as e:result,error=None,e
            self.signals.done.emit(key,result,error)
        future.add_done_callback(finished)

    def task_done(self,key,result,error):
        self.busy.discard(key);callback=self.callbacks.pop(key,None)
        if error:self.fail(error)
        elif callback:callback(result)
        elif result:self.message(result)
        if key=='search':self.search_button.setEnabled(True)
        if key=='downloads':self.download_button.setEnabled(True)
        if key=='firmware':self.flash_button.setEnabled(True)

    def build_guitar(self):
        tab=QWidget();outer=QVBoxLayout(tab)
        bar=QHBoxLayout();self.port=QComboBox();self.port.setMinimumWidth(260)
        bar.addWidget(self.port,1);bar.addWidget(self.button('Atualizar portas',self.scan_ports))
        bar.addWidget(self.button('Conectar',self.connect_device));bar.addWidget(self.button('Desconectar',self.disconnect_device))
        outer.addLayout(bar)
        self.connection_detail=QLabel('');self.connection_detail.setWordWrap(True);outer.addWidget(self.connection_detail)
        split=QSplitter();self.guitar=Guitar();self.guitar.selected.connect(self.select_action);split.addWidget(self.guitar)
        panel=QWidget();right=QVBoxLayout(panel);right.setContentsMargins(18,12,8,8)
        self.action_title=QLabel();self.action_title.setStyleSheet('font-size:21px;font-weight:600');right.addWidget(self.action_title)
        self.action_state=QLabel('Aguardando');right.addWidget(self.action_state)
        right.addWidget(QLabel('Terminal de sinal no ESP32'))
        self.pin=QComboBox()
        for pin in config.GPIO:self.pin.addItem('D'+str(pin),pin)
        right.addWidget(self.pin)
        right.addWidget(self.button('Usar este terminal',self.assign_pin))
        right.addWidget(self.button('Identificar pelo botão físico',self.learn))
        right.addWidget(self.button('Cancelar identificação',self.cancel_learn))
        note=QLabel('Para identificar: clique acima e aperte somente o botão indicado. Se o terminal já pertence a outra função, as duas trocam de lugar.');note.setWordWrap(True);right.addWidget(note)
        self.table=QTableWidget(9,3);self.table.setHorizontalHeaderLabels(['Função','Apertos','Segurado'])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellClicked.connect(lambda row,col:self.select_action(row))
        for i,label in enumerate(config.LABELS):
            for j,text in enumerate([label,'0','—']):self.table.setItem(i,j,QTableWidgetItem(text))
        right.addWidget(self.table,1)
        self.whammy=QCheckBox('Whammy físico instalado · D34');self.whammy.setChecked(self.profile['whammy']);self.whammy.toggled.connect(self.change_whammy)
        if sys.platform=='win32':
            self.whammy.setEnabled(False)
            self.whammy.setText('Whammy analógico · disponível no Linux')
        right.addWidget(self.whammy);self.analog=QProgressBar();self.analog.setRange(0,4095);right.addWidget(self.analog)
        right.addWidget(self.button('Abrir Clone Hero',self.launch_game))
        split.addWidget(panel);split.setStretchFactor(0,1);split.setStretchFactor(1,1);outer.addWidget(split,1)
        self.tabs.addTab(tab,'Guitarra');self.select_action(0)

    def build_setup(self):
        page=QWidget();box=QVBoxLayout(page);form=QFormLayout();self.fields={}
        for key,label,folder in [('game','Executável do Clone Hero',False),('game_data','Pasta de dados do jogo',True),('songs','Pasta de músicas',True)]:
            row=QWidget();line=QHBoxLayout(row);line.setContentsMargins(0,0,0,0)
            edit=QLineEdit(self.profile[key]);self.fields[key]=edit;line.addWidget(edit)
            line.addWidget(self.button('Escolher…',lambda checked=False,k=key,d=folder:self.choose_path(k,d)));form.addRow(label,row)
        box.addLayout(form)
        self.sfx=QCheckBox('Ativar efeito sonoro do whammy no jogo');self.sfx.setChecked(self.profile['whammy_sfx']);box.addWidget(self.sfx)
        self.auto=QCheckBox('Conectar automaticamente ao abrir o aplicativo');self.auto.setChecked(self.profile['auto_connect']);box.addWidget(self.auto)
        box.addWidget(self.button('Salvar caminhos e preferências',self.save_setup))
        box.addWidget(self.button('Aplicar configuração inicial no Clone Hero',self.prepare_game))
        help=QLabel('A configuração inicial mantém as demais opções e salva backup antes de ajustar Whammy SFX. Feche o jogo antes de aplicar.\n'
                    'Linux: controle virtual com cinco cores, duas palhetadas, Start/Select e eixo analógico opcional.\n'
                    'Windows: saída por teclado quando Clone Hero está em primeiro plano; mapear A/S/J/K/L, ↑/↓, Enter e H no jogo. '
                    'Whammy analógico no Windows ainda não está disponível.\n'
                    'No jogo, faça o mapeamento pelo menu de controles. O aplicativo configura a guitarra, não altera silenciosamente o perfil do jogador.')
        help.setWordWrap(True);box.addWidget(help)
        if sys.platform.startswith('linux'):box.addWidget(self.button('Configurar permissões do Linux…',self.permissions))
        else:box.addWidget(self.button('Driver USB CH340 · site oficial WCH',lambda:QDesktopServices.openUrl(QUrl('https://www.wch-ic.com/downloads/CH341SER_EXE.html'))))
        box.addWidget(QLabel('GPIO novo: firmware configurável v11 (opcional)'))
        fw=QLabel('O v10 atual já permite trocar funções entre os nove terminais conectados. O v11 permite escolher outros GPIOs da lista e grava a pinagem no ESP32. '
                  'O aplicativo desconecta antes de gravar. Mantenha todos os botões soltos e não remova o USB durante a gravação. GPIO15 deve ficar solto no boot.')
        fw.setWordWrap(True);box.addWidget(fw)
        box.addWidget(self.button('Preparar ferramentas de gravação · online',self.prepare_tools))
        self.flash_button=self.button('Instalar firmware configurável v11…',self.flash);box.addWidget(self.flash_button)
        box.addWidget(self.button('Manual do aplicativo · F1',self.open_manual))
        box.addStretch();scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);self.tabs.addTab(scroll,'Configuração')

    def build_music(self):
        page=QWidget();box=QVBoxLayout(page);top=QHBoxLayout();self.query=QLineEdit();self.query.setPlaceholderText('Banda ou música: Metallica, Numb, Nirvana…')
        self.query.returnPressed.connect(self.search_music);top.addWidget(self.query,1)
        self.difficulty=QComboBox()
        for label,value in [('Easy','easy'),('Medium','medium'),('Hard','hard'),('Expert','expert'),('Todas','')]:self.difficulty.addItem(label,value)
        top.addWidget(self.difficulty);self.search_button=self.button('Buscar online',self.search_music);top.addWidget(self.search_button);box.addLayout(top)
        note=QLabel('Catálogo online Chorus Encore. Os testes e a guitarra funcionam offline. Selecione as músicas para baixar da fonte pública do chart.');note.setWordWrap(True);box.addWidget(note)
        self.songs_table=QTableWidget(0,5);self.songs_table.setHorizontalHeaderLabels(['Baixar','Artista','Música','Guitarra','Charter'])
        self.songs_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.songs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);box.addWidget(self.songs_table,1)
        nav=QHBoxLayout();nav.addWidget(self.button('Página anterior',lambda:self.move_page(-1)));nav.addWidget(self.button('Próxima página',lambda:self.move_page(1)))
        nav.addWidget(self.button('Selecionar todas',self.check_all));nav.addWidget(self.button('Abrir fonte da selecionada',self.open_source));box.addLayout(nav)
        self.download_button=self.button('Baixar músicas marcadas',self.download_music);box.addWidget(self.download_button)
        self.download_log=QPlainTextEdit();self.download_log.setReadOnly(True);self.download_log.setMaximumHeight(130);box.addWidget(self.download_log)
        row=QHBoxLayout();row.addWidget(self.button('Abrir pasta de músicas',self.open_songs))
        row.addWidget(QLabel('Depois do download: no jogo, Settings → General → Scan Songs.'));box.addLayout(row)
        self.tabs.addTab(page,'Músicas · online')

    def build_logs(self):
        self.logs=QPlainTextEdit();self.logs.setReadOnly(True);self.tabs.addTab(self.logs,'Diagnóstico')

    def scan_ports(self):
        current=self.port.currentData() or self.profile['port'];self.port.clear();self.port.addItem('Automático · ESP32 USB','')
        for item in ports():self.port.addItem(item['label'],item['device'])
        index=self.port.findData(current);self.port.setCurrentIndex(max(0,index))

    def connect_device(self):
        self.engine.start(self.port.currentData() or '')

    def disconnect_device(self):
        self.engine.stop();self.message('Guitarra desconectada; comandos liberados.')

    def select_action(self,index):
        self.selected=index;self.guitar.active=index;self.guitar.update()
        self.action_title.setText(config.LABELS[index]);self.pin.setCurrentIndex(self.pin.findData(self.profile['pins'][index]))
        self.table.selectRow(index) if hasattr(self,'table') else None

    def assign_pin(self):
        self.commit_pins(config.swap_pin(self.profile['pins'],self.selected,self.pin.currentData()))

    def commit_pins(self,pins):
        profile=copy.deepcopy(self.profile);profile['pins']=pins
        try:self.engine.apply(profile);self.message('Aplicando pinagem… aguarde a confirmação. Mantenha os botões soltos.')
        except Exception as e:self.fail(e)

    def learn(self):
        state=self.engine.snapshot()
        if not state['connected'] or not state['firmware']:return self.fail(ValueError('Conecte a guitarra antes de identificar.'))
        self.learning=(self.selected,state['edge_seq']);self.message('Aperte somente: '+config.LABELS[self.selected]+'.')

    def cancel_learn(self):self.learning=None;self.message('Identificação cancelada.')

    def change_whammy(self,checked):
        profile=copy.deepcopy(self.profile);profile['whammy']=checked
        try:self.engine.apply(profile)
        except Exception as e:self.fail(e)

    def choose_path(self,key,folder):
        value=QFileDialog.getExistingDirectory(self,'Escolher pasta',self.fields[key].text()) if folder else QFileDialog.getOpenFileName(self,'Executável do Clone Hero',self.fields[key].text())[0]
        if value:self.fields[key].setText(value)

    def save_setup(self):
        profile=copy.deepcopy(self.profile)
        profile.update({k:v.text().strip() for k,v in self.fields.items()})
        profile.update(whammy_sfx=self.sfx.isChecked(),auto_connect=self.auto.isChecked(),port=self.port.currentData() or '')
        try:self.engine.apply(profile);self.message('Salvando preferências…')
        except Exception as e:self.fail(e)

    def prepare_game(self):
        self.save_setup()
        # Capture the current controls directly; engine applies profiles asynchronously.
        profile=copy.deepcopy(self.profile);profile.update({k:v.text().strip() for k,v in self.fields.items()});profile['whammy_sfx']=self.sfx.isChecked()
        self.task('prepare',lambda:game.prepare(profile))

    def launch_game(self):
        try:
            state=self.engine.snapshot()
            if not state['connected'] or not state['firmware'] or state['error'] or not state['output'].get('ready'):
                raise ValueError('Conecte a guitarra e confira a saída antes de abrir o jogo.')
            self.message(game.launch(self.profile))
        except Exception as e:self.fail(e)

    def permissions(self):
        # pkexec displays the desktop's own authentication prompt. Never run the app as root.
        command=['pkexec','bash',str(ROOT/'tools/setup-permissions.sh')]
        def run():
            r=external(command,capture_output=True,text=True,timeout=120)
            if r.returncode:raise ValueError(r.stderr or 'Configuração cancelada.')
            return r.stdout
        self.task('permissions',run)

    def flash(self):
        if self.busy.intersection({'tools','firmware'}):return self.message('Aguarde a preparação ou gravação em andamento.')
        port=self.port.currentData() or self.engine.snapshot().get('port')
        if not port:return self.fail(ValueError('Selecione a porta do ESP32.'))
        answer=QMessageBox.question(self,'Atualizar ESP32','Substituir o firmware pelo CONFIG v11?\nA pinagem inicial será a atual do projeto; depois você poderá alterá-la na tela. Se necessário, as ferramentas oficiais serão baixadas primeiro. Não remova o USB.')
        if answer!=QMessageBox.StandardButton.Yes:return
        self.engine.stop();self.flash_button.setEnabled(False)
        self.task('firmware',lambda:firmware.upload(port,self.signals.progress.emit))

    def prepare_tools(self):
        if self.busy.intersection({'tools','firmware'}):return self.message('Aguarde a preparação ou gravação em andamento.')
        self.task('tools',lambda:firmware.prepare(self.signals.progress.emit))

    def open_manual(self):
        try:
            path=manual.render()
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                raise ValueError('Abra o manual pelo arquivo: '+str(path))
        except Exception as e:self.fail(e)

    def search_music(self):
        self.page=1;self.perform_search()

    def move_page(self,delta):
        if 'search' in self.busy:return
        self.page=max(1,self.page+delta);self.perform_search()

    def perform_search(self):
        query=self.query.text();difficulty=self.difficulty.currentData();page=self.page
        self.search_button.setEnabled(False);self.message('Buscando no catálogo online…')
        self.task('search',lambda:music.search(query,difficulty,page),self.show_results)

    def show_results(self,rows):
        self.rows=rows;self.songs_table.setRowCount(len(rows))
        for i,c in enumerate(rows):
            check=QTableWidgetItem();check.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsSelectable);check.setCheckState(Qt.CheckState.Unchecked);self.songs_table.setItem(i,0,check)
            levels=[n['difficulty'] for n in (c.get('notesData') or {}).get('noteCounts',[]) if n.get('instrument')=='guitar' and n.get('count',0)>0]
            for j,value in enumerate([c.get('artist',''),c.get('name',''),', '.join(levels),c.get('charter','')],1):self.songs_table.setItem(i,j,QTableWidgetItem(str(value)))
        self.message(f'Página {self.page}: {len(rows)} charts. Confira artista, música e dificuldades antes de baixar.')

    def check_all(self):
        for i in range(self.songs_table.rowCount()):self.songs_table.item(i,0).setCheckState(Qt.CheckState.Checked)

    def open_source(self):
        index=self.songs_table.currentRow()
        if 0<=index<len(self.rows):
            fid=self.rows[index].get('applicationDriveId','')
            if fid:QDesktopServices.openUrl(QUrl('https://drive.google.com/open?id='+fid))

    def download_music(self):
        charts=[copy.deepcopy(c) for i,c in enumerate(self.rows) if self.songs_table.item(i,0).checkState()==Qt.CheckState.Checked]
        if not charts:return self.fail(ValueError('Marque pelo menos uma música.'))
        dest=self.fields['songs'].text().strip()
        if not dest:return self.fail(ValueError('Escolha a pasta de músicas em Configuração.'))
        self.download_button.setEnabled(False);self.download_log.clear()
        def run():
            results=[]
            for i,c in enumerate(charts):
                self.signals.progress.emit(f'Baixando {i+1}/{len(charts)}: {c["artist"]} — {c["name"]}')
                try:result=music.install(c,dest)
                except Exception as e:result='Não instalada: '+c['name']+' — '+str(e)
                results.append(result)
            return results
        def done(results):
            self.download_log.setPlainText('\n'.join(results));self.message('Fila concluída. Confira os resultados e execute Scan Songs no Clone Hero.')
        self.task('downloads',run,done)

    def open_songs(self):
        path=Path(self.fields['songs'].text()).expanduser();path.mkdir(parents=True,exist_ok=True);QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def refresh(self):
        state=self.engine.snapshot();self.profile=state['profile']
        if state['profile_revision']!=self.revision:
            self.revision=state['profile_revision']
            self.pin.setCurrentIndex(self.pin.findData(self.profile['pins'][self.selected]))
            self.message('Perfil salvo. Pinagem e preferências atualizadas.')
        self.guitar.mask=state['mask'];self.guitar.pins=self.profile['pins'];self.guitar.update()
        output=state['output'];self.status.setText(state['status'])
        text=(state['port']+' · ' if state['port'] else '')+('Saída pronta' if output.get('ready') else 'Saída aguardando')
        if state['error'] or output.get('error'):text+=' · '+(state['error'] or output.get('error'))
        self.connection_detail.setText(text)
        self.analog.setEnabled(self.profile['whammy']);self.analog.setValue(state['raw'] if self.profile['whammy'] else 0)
        self.analog.setFormat('%v / 4095' if self.profile['whammy'] else 'Whammy desativado')
        for i,bit in enumerate(config.BITS):
            duration=time.monotonic()-state['since'][i] if state['since'][i] else state['holds'][i]
            self.table.item(i,1).setText(str(state['counts'][i]));self.table.item(i,2).setText(f'{duration:.1f}s' if duration else '—')
        self.action_state.setText('PRESSIONADO' if state['mask']&config.BITS[self.selected] else 'Solto' if state['connected'] else 'Desconectado')
        if self.learning and state['edge_seq']>self.learning[1] and state['last_pin'] is not None:
            index,_=self.learning;self.learning=None;self.commit_pins(config.swap_pin(self.profile['pins'],index,state['last_pin']))
        logs='\n'.join(state['logs'])
        if self.logs.toPlainText()!=logs:self.logs.setPlainText(logs)

    def closeEvent(self,event):
        if self.busy:
            self.message('Aguarde a operação em andamento terminar antes de fechar.');event.ignore();return
        self.timer.stop();self.engine.stop();self.pool.shutdown(wait=False,cancel_futures=True);event.accept()

STYLE='''
QWidget { background:#111925; color:#e7edf6; font-family:Sans; font-size:13px; }
QPushButton { background:#22334b; border:1px solid #3c506b; border-radius:6px; padding:9px 13px; }
QPushButton:hover { background:#304766; } QPushButton:disabled {color:#68788b;}
QLineEdit,QComboBox,QPlainTextEdit,QTableWidget {background:#172334;border:1px solid #32445c;border-radius:4px;padding:5px;}
QHeaderView::section {background:#24344b;padding:7px;border:0;}
QTabBar::tab {padding:11px 22px;background:#182438;} QTabBar::tab:selected {background:#2b4358;color:#70edac;}
QTabWidget::pane {border:1px solid #304158;} QProgressBar {border:1px solid #32445c;border-radius:4px;text-align:center;height:20px;}
QProgressBar::chunk {background:#3d9e75;} QCheckBox {padding:7px 0;} QLabel {padding:2px;}
'''

def main():
    app=QApplication(sys.argv);app.setApplicationName('Guitar Lab');app.setOrganizationName('GuitarLab');app.setStyleSheet(STYLE)
    if '--self-test' in sys.argv:
        window=Window(auto=False);app.processEvents()
        assert window.tabs.count()==4
        assert (ROOT/'docs/manual.md').is_file()
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            assert 'data:image/png' in manual.render(Path(temp)/'manual.html').read_text(encoding='utf8')
        import esptool
        if (ROOT/'firmware/prebuilt/manifest.json').exists():firmware.prebuilt_images()
        window.close()
        return 0
    root=config.data_dir();root.mkdir(parents=True,exist_ok=True);lock=QLockFile(str(root/'window.lock'))
    if not lock.tryLock(0):
        QMessageBox.information(None,'Guitar Lab','O aplicativo já está aberto.');return 0
    window=Window();window.show();return app.exec()

if __name__=='__main__':raise SystemExit(main())
