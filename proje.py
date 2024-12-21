import webbrowser
import pandas as pd
from pyvis.network import Network
import random
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Excel dosyasını okuma
file_path = r"C:\\Users\\ÜLKÜ\\Desktop\\LabProje3\\PROLAB 3 - GÜNCEL DATASET.xlsx"

df = pd.read_excel(file_path)


def dugumolustur(network, orcid, name, articles, color, size, x, y):
    node = {
        "id": orcid,
        "label": name,
        "makele":articles,
        "color": color,
        "originalColor": color,
        "size": size,
        "x": x,
        "y": y,
        "physics": False,
        "shape": "dot",
        "font": {"color": "white", "size": 80},
    }
    network.nodes.append(node)


def kenarolustur(network, source, target, author_list):
    if source != target:
        source_articles = next((author[2] for author in author_list if author[0] == source), [])
        target_articles = next((author[2] for author in author_list if author[0] == target), [])
        ortak_makaleler = set(source_articles).intersection(set(target_articles))
        ortak_makale_sayisi = len(ortak_makaleler)

        if ortak_makale_sayisi > 0:
            edge_color = "#018786" if ortak_makale_sayisi == 1 else "yellow"
            edge = {
                "from": source,
                "to": target,
                "color": edge_color,
                "weight": ortak_makale_sayisi,
                "width": 6,
                "title": f"Ortak Makale Sayısı: {ortak_makale_sayisi}",
            }
            network.edges.append(edge)

            for author in author_list:
                if author[0] == source and target not in author[3]:  # Hedef yazar kaynak yazarın listesinde yoksa ekle
                    author[3].append(target)
                if author[0] == target and source not in author[3]:  # Kaynak yazar hedef yazarın listesinde yoksa ekle
                    author[3].append(source)


author_list = []  # orcid, name, makaleler , ortak yazarlar
added_authors = set()

for index, row in df.iterrows():
    author_name = row['author_name']
    orcid = row['orcid']
    coauthors = eval(row['coauthors'])

    if orcid not in added_authors:
        articles = df.loc[df['orcid'] == orcid, 'paper_title'].tolist()
        author_list.append([orcid, author_name, articles, []])
        added_authors.add(orcid)

    for coauthor in coauthors:
        coauthor = coauthor.strip()
        coauthor_orcid = f"null-{coauthor}" if not any(df['author_name'] == coauthor) else \
            df.loc[df['author_name'] == coauthor, 'orcid'].values[0]
        coauthor_articles = [row['paper_title']]

        for author in author_list:
            if author[0] == coauthor_orcid:
                author[2] = list(set(author[2] + coauthor_articles))  # Yeni makaleleri ekle
                break
            else:
                if coauthor_orcid != orcid and coauthor_orcid not in added_authors:  # Kendisiyle eklemeyi önle
                    author_list.append(
                        [coauthor_orcid, coauthor, coauthor_articles, []])  # Bağlantı sayısı başlangıçta 0
                    added_authors.add(coauthor_orcid)

net = Network(height="1080px", width="1920px", bgcolor="#222222")
positions = {}

makale_sayilari = [len(author[2]) for author in author_list]
ortalama_makale_sayisi = sum(makale_sayilari) / len(makale_sayilari)
alt_limit = ortalama_makale_sayisi * 0.80  # %20 altı
üst_limit = ortalama_makale_sayisi * 1.50  # %20 ile %50 arası
print(ortalama_makale_sayisi)

for author in author_list:
    orcid, name, articles, _ = author
    makale_sayisi = len(articles)

    # Makale sayılarına göre renk ve boyut ayarı
    if "null-" in orcid:
        # null ORCID'ler için renk tonu (yeni %30, %60 sınırları)
        if makale_sayisi < alt_limit:  # %30 altı
            node_size = 100
            node_color = "#FF80BF"  # Açık pembe (küçük düğüm)
        elif makale_sayisi > üst_limit:  # %30 ile %60 arası
            node_size = 400
            node_color = "#D5006D"  # Orta pembe (orta düğüm)
        else:  # %60 ve üstü
            node_size = 200
            node_color = "#FF66B2"  # Koyu pembe (büyük düğüm)

    else:
        # Diğer düğümler için renk ve boyut
        if makale_sayisi < alt_limit:  # %30 altı
            node_size = 100  # Küçük düğüm boyutu
            node_color = "#87CEFA"  # Açık mavi (küçük düğüm)
        elif makale_sayisi > üst_limit:  # %30 ile %60 arası
            node_size = 400  # Büyük düğüm boyutu
            node_color = "#0056b3"  # Orta mavi (orta düğüm)
        else:  # %60 ve üstü
            node_size = 200  # Orta düğüm boyutu
            node_color = "#007BFF"  # Koyu mavi (büyük düğüm)

    article_list = "\n".join([f"{i + 1}. {article}" for i, article in enumerate(articles)])
    x = random.uniform(-50000, 50000)
    y = random.uniform(-30000, 30000)
    positions[orcid] = (x, y)

    dugumolustur(net, orcid, name, article_list, node_color, node_size, x, y)

edges_set = set()

for index, row in df.iterrows():
    orcid = row['orcid']
    coauthors = eval(row['coauthors'])

    for coauthor in coauthors:
        coauthor = coauthor.strip()
        coauthor_orcid = f"null-{coauthor}" if not any(df['author_name'] == coauthor) else \
            df.loc[df['author_name'] == coauthor, 'orcid'].values[0]

        edge = tuple(sorted([orcid, coauthor_orcid]))

        if edge not in edges_set:
            kenarolustur(net, orcid, coauthor_orcid, author_list)
            edges_set.add(edge)

output_path = "network_graph.html"
net.write_html(output_path)

custom_js = """
<script type="text/javascript">
    var previouslySelectedNode = null; // Daha önce seçilmiş düğüm

    network.on("click", function (params) {
    if (params.nodes.length > 0) {
        var selectedNode = params.nodes[0];
        var selectedNodeData = network.body.data.nodes.get(selectedNode);

        const outputText = `Tıklanan Yazar:\n` +
            `ID: ${selectedNode}\n` +
            `Ad: ${selectedNodeData.label}\n` +
            `Makale(ler): \n${selectedNodeData.makele}`;
        document.getElementById('outputText').innerText = outputText;

        const outputElement = document.getElementById('outputText');
        outputElement.style.opacity = 0; // Animasyonu durdur
        outputElement.style.animation = 'none'; // Animasyonu sıfırla
        outputElement.offsetHeight; // DOM'u yeniden işleme al
        outputElement.style.animation = 'fadeInText 5s forwards'; // Yeniden başlat

        selectNodeAndHighlight(selectedNode); // Ortak fonksiyonu kullan
    }
    });

function handleShortestPath() {
    const orcid1 = document.getElementById("inputForFirstIster1").value;
    const orcid2 = document.getElementById("inputForFirstIster2").value;

    if (!orcid1 || !orcid2) {
        alert("Lütfen her iki yazar için de ORCID ID'si giriniz!");
        return;
    }

    // Flask API'ye istek gönder
    fetch(`/shortest-path/${orcid1}/${orcid2}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('outputText').innerHTML = `<p>${data.error}</p>`;
            } else {
                const shortestPath = data.shortest_path;
                const queueStates = data.queue_states;

                // Grafiksel çıktıyı oluşturma
                let outputHTML = `<h3>En Kısa Yol</h3>`;
                outputHTML += `<p>${shortestPath.join(" -> ")}</p>`;

                outputHTML += `<h3>Kuyruğun Adım Adım Durumu</h3>`;
                queueStates.forEach((state, index) => {
                    outputHTML += `<p>Adım ${index + 1}: ${state.map(path => path.join(" -> ")).join(", ")}</p>`;
                });

                // Soldaki beyaz alana yazdırma
                document.getElementById('outputText').innerHTML = outputHTML;
            }
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerHTML = `<p>Bağlantı bilgisi alınamadı!</p>`;
        });
}

var selectedNodes = []; // Seçilen düğümlerin listesi

function selectNodeAndHighlight2(nodeId) {
    // Eğer düğüm zaten seçiliyse, işleme devam etme
    if (selectedNodes.includes(nodeId)) {
        return;
    }

    // Yeni düğüm seçildiyse, onu seçilenler listesine ekle
    selectedNodes.push(nodeId);

    // Seçilen düğümün orijinal rengini al
    var node = network.body.data.nodes.get(nodeId);
    var originalColor = node.originalColor || node.color; // Eğer originalColor yoksa, mevcut renk kullan

    // Seçilen düğümün rengini değiştir
    network.body.data.nodes.update({ id: nodeId, color: { background: 'green' } });

    // Kenarları da güncelle
    edges.forEach(function (edge) {
        if (edge.from === nodeId || edge.to === nodeId) {
            var edgeOriginalColor = edge.weight > 1 ? "yellow" : "#018786";
            network.body.data.edges.update({ id: edge.id, color: edgeOriginalColor });

            var connectedNode = edge.from === nodeId ? edge.to : edge.from;
            // Bağlantılı düğümün rengini koru
            var connectedOriginalColor = network.body.data.nodes.get(connectedNode).originalColor || network.body.data.nodes.get(connectedNode).color;
            network.body.data.nodes.update({ id: connectedNode, color: connectedOriginalColor });
        }
    });

    // Önceki seçili düğümün rengini geri al
    if (selectedNodes.length > 1) {
        var previousNodeId = selectedNodes[0]; // İlk seçilen düğüm
        var previousNode = network.body.data.nodes.get(previousNodeId);
        var previousOriginalColor = previousNode.originalColor || previousNode.color;

        network.body.data.nodes.update({ id: previousNodeId, color: previousOriginalColor });

        edges.forEach(function (edge) {
            if (edge.from === previousNodeId || edge.to === previousNodeId) {
                var edgeOriginalColor = edge.weight > 1 ? "yellow" : "#018786";
                network.body.data.edges.update({ id: edge.id, color: edgeOriginalColor });

                var connectedNode = edge.from === previousNodeId ? edge.to : edge.from;
                var connectedOriginalColor = network.body.data.nodes.get(connectedNode).originalColor || network.body.data.nodes.get(connectedNode).color;
                network.body.data.nodes.update({ id: connectedNode, color: connectedOriginalColor });
            }
        });

        // İlk seçili düğümü listeden çıkar
        selectedNodes.shift();
    }
}

    function selectNodeAndHighlight(nodeId) {
    if (previouslySelectedNode === nodeId) {
        return; // Aynı düğüm tekrar seçilemez
    }
    if (previouslySelectedNode !== null) {
        // Önceki düğüm ve kenarları varsayılan renklere döndür
        var originalColor = network.body.data.nodes.get(previouslySelectedNode).originalColor;
        network.body.data.nodes.update({ id: previouslySelectedNode, color: originalColor });

        edges.forEach(function (edge) {
            if (edge.from === previouslySelectedNode || edge.to === previouslySelectedNode) {
                var edgeOriginalColor = edge.weight > 1 ? "yellow" : "#018786";
                network.body.data.edges.update({ id: edge.id, color: edgeOriginalColor });

                var connectedNode = edge.from === previouslySelectedNode ? edge.to : edge.from;
                var connectedOriginalColor = network.body.data.nodes.get(connectedNode).originalColor;
                network.body.data.nodes.update({ id: connectedNode, color: connectedOriginalColor });
            }
        });
    }

    // Yeni düğümü seç ve vurgula
    edges.forEach(function (edge) {
        if (edge.from === nodeId || edge.to === nodeId) {
            network.body.data.edges.update({ id: edge.id, color: "red" });

            var connectedNode = edge.from === nodeId ? edge.to : edge.from;
            network.body.data.nodes.update({ id: connectedNode, color: "white" });
        }
    });

    network.body.data.nodes.update({ id: nodeId, color: "yellow" });
    previouslySelectedNode = nodeId;
}

    function showMostConnectedAuthor() {
    fetch("/most-connected-author")
        .then(response => response.json())
        .then(data => {
            // Çıktıyı yazma
            const outputText = `En Fazla Bağlantıya Sahip Yazar:\n` +
                `Ad: ${data.author_name}\n` +
                `ID: ${data.author_id}\n` +
                `Bağlantı Sayısı: ${data.connections}`;
            document.getElementById('outputText').innerText = outputText;

            // Animasyonu sıfırlayıp yeniden başlatmak için
            const outputElement = document.getElementById('outputText');
            outputElement.style.opacity = 0; // Animasyonu durdur
            outputElement.style.animation = 'none'; // Animasyonu sıfırla
            outputElement.offsetHeight; // DOM'u yeniden işleme al
            outputElement.style.animation = 'fadeInText 5s forwards'; // Yeniden başlat

            // İlgili düğümü seç ve vurgula
            selectNodeAndHighlight(data.author_id); // Ortak fonksiyonu kullan
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerText = "En fazla bağlantıya sahip yazar bilgisi alınamadı!";
        });
}


let currentQueue = [];

function showQueueForAuthor() {
    const authorId = document.getElementById("authorIdInput").value;
    if (!authorId) {
        alert("Yazar ID'si boş olamaz!");
        return;
    }
    
    fetch(`/queue-for-author/${authorId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('outputText').innerText = data.error;
            } else {
                // Çıktıyı düzenle
                let output = `Seçilen Yazar: ${data.target_author.name} (ID: ${data.target_author.orcid})\n\nKuyruk Durumu:\n`;
                data.queue.forEach((author, index) => {
                    output += `${index + 1}. ${author.name} (ID: ${author.orcid}, Makale Sayısı: ${author.articles})\n`;
                });
                document.getElementById('outputText').innerText = output;

                // Kuyruk verilerini kaydet
                currentQueue = data.queue;
            }

            // Animasyonu sıfırlayıp yeniden başlatmak için
            const outputText = document.getElementById('outputText');
            outputText.style.opacity = 0;
            outputText.style.animation = 'none';
            outputText.offsetHeight;
            outputText.style.animation = 'fadeInText 5s forwards';

            selectNodeAndHighlight(authorId);
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerText = "Yazar kuyruğu bilgisi alınamadı!";
        });

    // Ekleme ve çıkarma butonlarını göster
    document.getElementById("queueControls").style.display = "block";
}

function addAuthorToQueue() {
    const authorId = document.getElementById("addAuthorId").value;
    if (!authorId) {
        alert("Yazar ID'si giriniz!");
        return;
    }

    // Kuyruğa yeni yazar ekleyin
    fetch(`/add-author-to-queue/${authorId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);  // Yazar eklenemedi uyarısını göster
        } else {
            // Kuyruğa yeni yazar ekleyin
            currentQueue = data.queue;  // API'den dönen kuyruğu kullanın
            updateQueueDisplay();
            alert("Yazar başarıyla kuyruğa eklendi!");
        }
    })
    .catch(error => {
        console.error("Hata:", error);
        alert("Yazar eklenemedi!");
    });
}



function updateQueueDisplay() {
    let output = `Kuyruk Durumu:\n`;
    currentQueue.forEach((author, index) => {
        output += `${index + 1}. ${author.name} (ID: ${author.orcid}, Makale Sayısı: ${author.articles})\n`;
    });
    document.getElementById('outputText').innerText = output;

    // Animasyonu sıfırlayıp yeniden başlatmak için
    const outputText = document.getElementById('outputText');
    outputText.style.opacity = 0;
    outputText.style.animation = 'none';
    outputText.offsetHeight;
    outputText.style.animation = 'fadeInText 5s forwards';
}


function removeAuthorFromQueue() {
    const authorId = document.getElementById("removeAuthorId").value;
    if (!authorId) {
        alert("Yazar ID'si giriniz!");
        return;
    }

    // Kuyruktan yazar çıkarma isteği gönderin
    fetch(`/remove-author-from-queue/${authorId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);  // Yazar kuyruğa eklenmedi uyarısını göster
        } else {
            // Kuyruğu güncelleyin
            currentQueue = data.queue;  // API'den dönen kuyruğu kullanın
            updateQueueDisplay();
            alert("Yazar başarıyla çıkarıldı!");
        }
    })
    .catch(error => {
        console.error("Hata:", error);
        alert("Yazar çıkarılamadı!");
    });
}



function handleFifthIster() {
    const orcid = document.getElementById("inputForFifthIster").value;

    if (!orcid) {
        alert("5. İster için ORCID ID giriniz!");
        return;
    }

    // Flask API'ye istek gönder
    fetch(`/get-author-info/${orcid}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('outputText').innerText = "Yazar bilgileri alınamadı!";
            } else {
                // Çıktıyı yazma
                const outputText = `Girilen Yazar:\n` +
                    `Ad: ${data.author_name}\n` +
                    `ID: ${orcid}\n` +
                    `Ortak Yazar Sayısı: ${data.coauthors_count}`;
                document.getElementById('outputText').innerText = outputText;

                // Animasyonu sıfırlayıp yeniden başlatmak için
                const outputElement = document.getElementById('outputText');
                outputElement.style.opacity = 0; // Animasyonu durdur
                outputElement.style.animation = 'none'; // Animasyonu sıfırla
                outputElement.offsetHeight; // DOM'u yeniden işleme al
                outputElement.style.animation = 'fadeInText 5s forwards'; // Yeniden başlat
            }
            selectNodeAndHighlight(orcid);
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerText = "Yazar bilgileri alınamadı!";
        });
}

function handleLongestPath() {
    const userInput = document.getElementById("inputForLongestPath").value;

    if (!userInput) {
        alert("Lütfen bir ORCID ID giriniz!");
        return;
    }

    // Flask API'ye istek gönder
    fetch(`/longest-path/${userInput}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Yazar bilgisi alınamadı!");
            }
            return response.json();
        })
        .then(data => {
            console.log("Gelen Veri:", data); // Gelen veriyi kontrol edin

            if (data.error) {
                document.getElementById('outputText').innerHTML = `<p>${data.error}</p>`;
            } else {
                // Gelen mesajı beyaz ekrana yazdır
                const output = `<p>${data.message}</p>`;
                document.getElementById('outputText').innerHTML = output;
            }
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerHTML = `<p>Bir hata oluştu: ${error.message}</p>`;
        });
}



   function clearOutput() {
    const outputText = document.getElementById('outputText');
    outputText.style.opacity = 0; // Çıktıyı sıfırlarken animasyonu durdur
    outputText.innerText = ''; // Çıktıyı sıfırla

    // Animasyonu sıfırlayıp yeniden başlatmak için
    outputText.style.animation = 'none'; // Önce animasyonu durdur
    outputText.offsetHeight; // DOM'u yeniden işleme al
    outputText.style.animation = 'fadeInText 5s forwards'; // Yeniden başlat
}

</script>


<style>
   /* Sol taraf için stil */
.output-container {
    position: fixed;
    top: 6%;
    left: 10px;
    width: 450px;
    height: 85%;
    background: linear-gradient(135deg, #f1f1f1 0%, #e0e0e0 100%);
    border: none;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 15px 30px rgba(0, 0, 0, 0.2);
    overflow-y: auto;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
    color: #333;
    transition: box-shadow 0.3s ease-in-out;
    opacity: 0;
    animation: fadeIn 7s forwards; /* Ekran yüklendiğinde içerik yavaşça belirecek */
}

.output-container:hover {
    box-shadow: 0px 20px 40px rgba(0, 0, 0, 0.3);
}

/* Çıktı metni için stil */
#outputText {
    font-size: 18px;
    color: #444;
    line-height: 1.6;
    word-wrap: break-word;
    overflow-wrap: break-word;
    opacity: 0;
    animation: fadeInText 7s forwards; /* Metin yazıları yavaşça belirecek */
}

/* Butonlar için Stil */
.ister-button {
    display: block;
    width: 160px; /* Genişlik artırıldı */
    height: 60px; /* Yükseklik aynı */
    margin: 10px auto;
    padding: 15px; /* İç boşluk aynı */
    background-color: #018786;
    color: white;
    border: none;
    text-align: center;
    border-radius: 5px;
    font-size: 20px; /* Yazı boyutu aynı */
    cursor: pointer;
    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.3);
    transition: background-color 0.3s ease, transform 0.2s ease;
}

.ister-button:hover {
    background-color: #005f63;
    transform: translateY(-3px);
}

/* Sağdaki Kutunun Stili */
.ister-container {
    position: fixed;
    top: 6%;
    right: 10px;
    width: 220px; /* Genişlik artırıldı */
    height: 85%;
    overflow-y: auto;
    background-color: #f8f9fa;
    border: 1px solid #ddd;
    padding: 20px; /* İç boşluk aynı */
    border-radius: 15px;
    box-shadow: 0px 8px 12px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    animation: fadeIn 7s forwards;
}

/* Input Kutusu */
.input-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 10px;
    width: 90%; /* Konteynır genişliği kutu ile uyumlu hale getirildi */
}

.input-container input {
    width: 90%; /* Genişlik kutuya göre ayarlandı */
    padding: 10px; /* İç boşluk artırıldı */
    font-size: 16px; /* Yazı boyutu aynı */
    border-radius: 5px;
    border: 1px solid #ccc;
    box-sizing: border-box;
}

.input-container button {
    width: 90%; /* Genişlik kutuya göre ayarlandı */
    height: 45px; /* Yükseklik artırıldı */
    font-size: 16px; /* Yazı boyutu aynı */
}

/* Küçük Buton */
.small-button {
    font-size: 16px;
    padding: 8px; /* İç boşluk artırıldı */
    margin-top: 10px; /* Daha düzgün görünüm için üst boşluk artırıldı */
    background-color: #027a73;
    width: 90%; /* Genişlik kutuya göre ayarlandı */
}

.small-button:hover {
    background-color: #005f63;
}

/* Fade-in animasyonu */
@keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

@keyframes fadeInText {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

</style>

<div class="output-container" id="outputContainer">
    <h3>Çıktı:</h3>
    <p id="outputText">Çıktı burada görünecek...</p>
</div>

<div class="ister-container">
    
    <!-- 1. İSTER için metin girişi -->
    <div class="input-container">
        <input type="text" id="inputForFirstIster1" placeholder="1. Yazar ORCID ID">
        <input type="text" id="inputForFirstIster2" placeholder="2. Yazar ORCID ID">
        <button class="ister-button small-button" onclick="handleShortestPath()">Göster</button>
    </div>

    <!-- Yazar ID'si girişi için kapsayıcı div -->
    <div class="input-container">
        <input type="text" id="authorIdInput" placeholder="2.İster için Yazar ID'si giriniz">
        <button class="ister-button small-button" onclick="showQueueForAuthor()">Göster</button>
    </div>

    <!-- Eklemek ve Çıkarmak için alanlar -->
    <div id="queueControls" style="display:none;">
        <div class="input-container">
            <input type="text" id="addAuthorId" placeholder="Ekleme için Yazar ID'si">
            <button class="ister-button small-button" onclick="addAuthorToQueue()">Ekle</button>
        </div>
        <div class="input-container">
            <input type="text" id="removeAuthorId" placeholder="Çıkarma için Yazar ID'si">
            <button class="ister-button small-button" onclick="removeAuthorFromQueue()">Çıkar</button>
        </div>
    </div>

    <button class="ister-button" onclick="callPythonFunction(3)">3. İSTER</button>
    <button class="ister-button" onclick="callPythonFunction(4)">4. İSTER</button>
    
    <!-- 5. İSTER için metin girişi -->
    <div class="input-container">
        <input type="text" id="inputForFifthIster" placeholder="5. İster için Yazar ID'si giriniz">
        <button class="ister-button small-button" onclick="handleFifthIster()">Göster</button>
    </div>
    
    <button class="ister-button" onclick="showMostConnectedAuthor()">6. İSTER</button>
    
    <!-- 7. İSTER için metin girişi -->
    <div class="input-container">
        <input id="inputForLongestPath" type="text" placeholder="7. İster için ORCID ID giriniz" />
        <button class="ister-button small-button" onclick="handleLongestPath()">En Uzun Yol Hesapla</button>
    </div>

    <button class="ister-button" onclick="clearOutput()">Çıktıyı Sıfırla</button>
</div>


<button onclick="document.documentElement.requestFullscreen()" style="
    position: fixed;
    bottom: 10px;
    left: 10px;
    padding: 10px 20px;
    background-color: #018786;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    z-index: 9999;
    animation: fadeIn 7s forwards;
">Tam Ekran</button>

"""

print(f"Toplam düğüm sayısı: {len(author_list)}")
print(f"Toplam kenar sayısı: {len(net.edges)}")

with open(output_path, "r", encoding="utf-8") as file:
    html_content = file.read()

if "</body>" in html_content:
    html_content = html_content.replace("</body>", f"{custom_js}</body>")

with open(output_path, "w", encoding="utf-8") as file:
    file.write(html_content)


kuyruk = []

def kuyruk_islemleri_2Ister(author_list, target_author_id):
    global kuyruk

    # Yazarın düğüm ağırlığını ve işbirlikçilerini bul
    target_author = next((author for author in author_list if author[0] == target_author_id), None)

    if not target_author:
        return {"error": f"Yazar ID'si {target_author_id} bulunamadı."}

    # İşbirliği yapan yazarları bul ve düğüm ağırlıklarına göre sıralama
    collaborations = target_author[3]  # İşbirliği yaptığı yazarlar
    collaboration_data = [
        (author[0], author[1], len(author[2]))  # (orcid, name, makale_sayısı)
        for author in author_list
        if author[0] in collaborations
    ]

    # Manuel sıralama (Bubble sort kullanıyoruz)
    for i in range(len(collaboration_data)):
        for j in range(len(collaboration_data) - 1 - i):
            # Makale sayısına göre karşılaştırma yap ve yer değiştir
            if collaboration_data[j][2] < collaboration_data[j + 1][2]:
                # Yazar bilgilerini ve makale sayısını değiştir
                collaboration_data[j], collaboration_data[j + 1] = collaboration_data[j + 1], collaboration_data[j]

    # Kuyruğu doldur
    kuyruk.clear()
    kuyruk.extend([{"orcid": author[0], "name": author[1], "articles": author[2]} for author in collaboration_data])

    return {
        "target_author": {"orcid": target_author[0], "name": target_author[1]},
        "queue": kuyruk,
    }


@app.route("/add-author-to-queue/<author_id>", methods=["POST"])
def add_author_to_queue(author_id):
    global kuyruk, author_list

    # Yazarın mevcut olup olmadığını kontrol et
    author = next((author for author in author_list if author[0] == author_id), None)
    if not author:
        return jsonify({"error": "Yazar bulunamadı!"}), 404

    # Kuyrukta yazar var mı kontrol et
    if any(item["orcid"] == author_id for item in kuyruk):
        return jsonify({"error": f"Kuyrukta zaten {author[1]} isimli yazar mevcut!"}), 400

    # Yeni yazar bilgisi
    new_author = {
        "orcid": author[0],
        "name": author[1],
        "articles": len(author[2]),  # Makale sayısını alıyoruz
        "collaborators": author[3]   # İşbirliği yaptığı diğer yazarlar
    }

    # Kuyruğa ekleme ve sıralama
    kuyruk.append(new_author)
    kuyruk.sort(key=lambda x: x["articles"], reverse=True)

    return jsonify({"message": f"{new_author['name']} başarıyla kuyruğa eklendi!", "queue": kuyruk})


@app.route("/remove-author-from-queue/<author_id>", methods=["POST"])
def remove_author_from_queue(author_id):
    global kuyruk, author_list

    # Kuyruktan çıkarma işlemi
    author = next((item for item in kuyruk if item["orcid"] == author_id), None)
    if not author:
        return jsonify({"error": f"Kuyrukta {author_id} ID'li yazar bulunamadı!"}), 404

    # Yazar çıkarma işlemi
    kuyruk = [item for item in kuyruk if item["orcid"] != author_id]

    return jsonify({"message": f"{author['name']} başarıyla kuyruktan ve ana listeden çıkarıldı!", "queue": kuyruk})


@app.route("/queue-for-author/<author_id>", methods=["GET"])
def queue_for_author(author_id):
    result = kuyruk_islemleri_2Ister(author_list, author_id)
    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


# Fonksiyon: En çok bağlantı kuran yazarı bulma
def en_cok_baglanti_kuran_yazar(author_list):
    most_connected_author = max(author_list, key=lambda x: len(x[3]))
    return most_connected_author

@app.route("/most-connected-author")
def most_connected_author():
    most_connected = en_cok_baglanti_kuran_yazar(author_list)
    return {
        "author_name": most_connected[1],
        "author_id": most_connected[0],
        "connections": len(most_connected[3]),
    }

@app.route('/get-author-info/<orcid>', methods=['GET'])
def get_author_info(orcid):
    # İlgili yazarı bul
    author = next((author for author in author_list if author[0] == orcid), None)
    if not author:
        return jsonify({"error": "Yazar bulunamadı!"}), 404

    # Ortak yazarlar listesinin uzunluğunu hesapla
    coauthors_count = len(author[3])
    return jsonify({
        "author_name": author[1],  # Yazar adı
        "coauthors_count": coauthors_count  # Ortak yazar sayısı
    })

@app.route('/shortest-path/<orcid1>/<orcid2>', methods=['GET'])
def find_shortest_path(orcid1, orcid2):
    from collections import defaultdict, deque

    # Yazarlar arasındaki bağlantıları içeren bir grafik oluştur
    graph = defaultdict(list)

    # Örnek grafik bağlantılarını doldur (author_list'ten veri çektiğimizi varsayıyoruz)
    for author in author_list:
        for coauthor in author[3]:
            graph[author[0]].append((coauthor, 1))  # Kenar ağırlığını 1 olarak varsayıyoruz
            graph[coauthor].append((author[0], 1))

    # Bağlantı kontrolü
    if orcid1 not in graph or orcid2 not in graph:
        return jsonify({"error": "Yazarlar arasında bağlantı bulunamadı!"}), 404

    # Dijkstra Algoritması
    def dijkstra_with_steps(graph, start, goal):
        queue = deque([[start]])
        visited = set()
        path_weights = {start: 0}
        paths = []  # Her adımda kuyruğun durumu

        while queue:
            path = queue.popleft()
            node = path[-1]
            paths.append(list(queue))  # Kuyruğun anlık durumu

            if node == goal:
                return path, paths

            if node not in visited:
                visited.add(node)
                for neighbor, weight in graph[node]:
                    if neighbor not in visited:
                        new_path = list(path)
                        new_path.append(neighbor)
                        queue.append(new_path)

                        # Ağırlığı güncelle
                        new_weight = path_weights[node] + weight
                        if neighbor not in path_weights or new_weight < path_weights[neighbor]:
                            path_weights[neighbor] = new_weight

        return None, paths

    # En kısa yol ve adım adım kuyruk durumlarını hesapla
    shortest_path, queue_states = dijkstra_with_steps(graph, orcid1, orcid2)

    if shortest_path:
        return jsonify({
            "shortest_path": shortest_path,
            "queue_states": queue_states,
            "authors_visited": shortest_path
        })
    else:
        return jsonify({"error": "Yazarlar arasında bağlantı bulunamadı!"}), 404


@app.route('/longest-path/<orcid>', methods=['GET'])
def longest_path(orcid):
    # Yazardan başlayarak DFS kullanarak en uzun yolu bul
    def dfs(node, visited):
        visited.add(node)  # Düğümü ziyaret edilmiş olarak işaretle
        max_length = 0  # En uzun yolun başlangıç değeri

        for neighbor in graph.get(node, []):  # Komşular üzerinde iterasyon yap
            if neighbor not in visited:  # Eğer düğüm daha önce ziyaret edilmediyse
                length = dfs(neighbor, visited) + 1  # Rekürsif olarak derinliği artır
                max_length = max(max_length, length)  # Maksimum uzunluğu güncelle

        visited.remove(node)  # Geriye dönerken düğümü tekrar kullanılabilir hale getir
        return max_length

    # Yazarın varlığını kontrol et
    author_exists = any(author[0] == orcid for author in author_list)
    if not author_exists:
        return jsonify({"error": "Bu ID'de bir yazar yok!"}), 404

    # `author_list` içinden grafiği oluştur
    graph = {}
    for author in author_list:
        orcid_id = author[0]  # Yazarın ORCID ID'si
        co_authors = author[3]  # Yazarın ortak yazarlarının listesi
        graph[orcid_id] = co_authors  # Grafiğe ekle

    # DFS için ziyaret edilen düğümleri tutacak set
    visited = set()

    # DFS kullanarak en uzun yolu bul
    longest_path_length = dfs(orcid, visited)

    # Sonuçları döndür
    return jsonify({
        "message": f"En uzun yol uzunluğu: {longest_path_length}",
        "start_node": orcid,
        "graph": graph
    })



@app.route("/")
def index():
    with open(output_path, "r", encoding="utf-8") as f:
        graph_html = f.read()
    return render_template_string(graph_html)


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False)
