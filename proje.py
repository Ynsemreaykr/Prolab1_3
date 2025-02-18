import webbrowser
import pandas as pd
from pyvis.network import Network
import random
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

file_path = r"C:\Users\ÜLKÜ\Desktop\LabProje3\PROLAB 3 - GÜNCEL DATASET.xlsx"

df = pd.read_excel(file_path)


def dugumolustur(network, orcid, name, articles, color, size, x, y):
    node = {
        "id": orcid,
        "label": name,
        "makele": articles,
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
                if author[0] == source and target not in author[3]:
                    author[3].append(target)
                if author[0] == target and source not in author[3]:
                    author[3].append(source)


author_list = []
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
                author[2] = list(set(author[2] + coauthor_articles))
                break
            else:
                if coauthor_orcid != orcid and coauthor_orcid not in added_authors:
                    author_list.append(
                        [coauthor_orcid, coauthor, coauthor_articles, []])
                    added_authors.add(coauthor_orcid)

net = Network(height="1080px", width="1920px", bgcolor="#222222")
positions = {}

makale_sayilari = [len(author[2]) for author in author_list]
ortalama_makale_sayisi = sum(makale_sayilari) / len(makale_sayilari)
alt_limit = ortalama_makale_sayisi * 0.80
üst_limit = ortalama_makale_sayisi * 1.50
print(ortalama_makale_sayisi)

for author in author_list:
    orcid, name, articles, _ = author
    makale_sayisi = len(articles)

    if "null-" in orcid:
        if makale_sayisi < alt_limit:
            node_size = 100
            node_color = "#FF80BF"
        elif makale_sayisi > üst_limit:
            node_size = 400
            node_color = "#D5006D"
        else:
            node_size = 200
            node_color = "#FF66B2"

    else:
        if makale_sayisi < alt_limit:
            node_size = 100
            node_color = "#87CEFA"
        elif makale_sayisi > üst_limit:
            node_size = 400
            node_color = "#0056b3"
        else:
            node_size = 200
            node_color = "#007BFF"

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
        outputElement.style.opacity = 0;  
        outputElement.style.animation = 'none'; 
        outputElement.offsetHeight; 
        outputElement.style.animation = 'fadeInText 5s forwards'; 

        selectNodeAndHighlight(selectedNode); 
    }
    });


function handleShortestPath() {
    const orcid1 = document.getElementById("inputForFirstIster1").value;
    const orcid2 = document.getElementById("inputForFirstIster2").value;

    if (!orcid1 || !orcid2) {
        alert("Lütfen her iki yazar için de ORCID ID'si giriniz!");
        return;
    }

    fetch(`/shortest-path/${orcid1}/${orcid2}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('outputText').innerHTML = `<p>${data.error}</p>`;
            } else {
                const shortestPath = data.shortest_path;
                const queueStates = data.queue_states;
                const visitedQueue = data.visited_queue;

                let outputHTML = `<h3>En Kısa Yol</h3>`;
                outputHTML += `<p>${shortestPath.join(" -> ")}</p>`;

                 outputHTML += `<h3>Ziyaret Edilen Yazarlar</h3>`;
                outputHTML += `<p>${visitedQueue.map((node, index) => {
                    let color = "black";  
                    if (index < visitedQueue.length - 1) {
                        return `<span style="color:${color};">${node}</span><span style="color:red;">, </span>`;
                    } else {
                        return `<span style="color:${color};">${node}</span>`;  
                    }
                }).join('')}</p>`;

                outputHTML += `<h3>Kuyruğun Adım Adım Durumu</h3>`;
                queueStates.forEach((state, index) => {
                    outputHTML += `<p>Adım ${index + 1}: ${state.map(path => path.join(" -> ")).join(", ")}</p>`;
                });

                document.getElementById('outputText').innerHTML = outputHTML;

                resetHighlights();
                highlightShortestPath(shortestPath);
            }
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerHTML = `<p>Bağlantı bilgisi alınamadı!</p>`;
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
                let output = `Seçilen Yazar: ${data.target_author.name} (ID: ${data.target_author.orcid})\n\nKuyruk Durumu:\n`;
                data.queue.forEach((author, index) => {
                    output += `${index + 1}. ${author.name} (ID: ${author.orcid}, Makale Sayısı: ${author.articles})\n`;
                });
                document.getElementById('outputText').innerText = output;

                currentQueue = data.queue;
            }

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

    document.getElementById("queueControls").style.display = "block";
}
function addAuthorToQueue() {
    const authorId = document.getElementById("addAuthorId").value;
    if (!authorId) {
        alert("Yazar ID'si giriniz!");
        return;
    }

    fetch(`/add-author-to-queue/${authorId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error); 
        } else {
            currentQueue = data.queue;  
            updateQueueDisplay();
            alert("Yazar başarıyla kuyruğa eklendi!");
        }
    })
    .catch(error => {
        console.error("Hata:", error);
        alert("Yazar eklenemedi!");
    });
}
function removeAuthorFromQueue() {
    const authorId = document.getElementById("removeAuthorId").value;
    if (!authorId) {
        alert("Yazar ID'si giriniz!");
        return;
    }

    fetch(`/remove-author-from-queue/${authorId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);  
        } else {
            currentQueue = data.queue;  
            updateQueueDisplay();
            alert("Yazar başarıyla çıkarıldı!");
        }
    })
    .catch(error => {
        console.error("Hata:", error);
        alert("Yazar çıkarılamadı!");
    });
}




function deleteAuthor() {
    const orcidInput = document.getElementById("orcidInput");
    const orcid = orcidInput.value.trim();
    if (!orcid) {
        alert("Lütfen ORCID ID'si giriniz.");
        return;
    }

    fetch('/delete-author', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ orcid: orcid })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById("outputText").innerHTML = `<p style="color: red;">Hata: ${data.error}</p>`;
        } else {
            const bstData = data.inorder_bst;

            console.log("Silme sonrası ağaç verisi:", bstData);

            const treeHTML = generateTreeHTML(bstData);
            document.getElementById("outputText").innerHTML = treeHTML; 
        }
    })
    .catch(error => {
        console.error("Hata:", error);
        document.getElementById("outputText").innerHTML = `<p style="color: red;">Bir hata oluştu. Lütfen tekrar deneyin.</p>`;
    });
}
function createBST() {
    fetch('/bst-from-shortest-path')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById("outputText").innerHTML = `<p style="color: red;">Hata: ${data.error}</p>`;
            } else {
                const bstData = data.inorder_bst; 
                const treeHTML = generateTreeHTML(bstData);
                document.getElementById("outputText").innerHTML = treeHTML; 
            }
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById("outputText").innerHTML = `<p style="color: red;">Bir hata oluştu. Lütfen tekrar deneyin.</p>`;
        });
}



function handleShortestPathForCollaborators() {
    const orcid = document.getElementById("inputForAWriter").value;

    if (!orcid) {
        alert("Lütfen A yazarı için ORCID ID'si giriniz!");
        return;
    }

    fetch(`/shortest-path-for-collaborators/${orcid}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data);  
            if (data.error) {
                document.getElementById('outputText').innerHTML = `<p>${data.error}</p>`;
            } else {
                const shortestPaths = data.shortest_paths;
                const queueStates = data.queue_states;
                resetHighlights();
                let outputHTML = `<h3>En Kısa Yol</h3>`;
                for (const [author, path] of Object.entries(shortestPaths)) {
                    outputHTML += `<p>${author}: ${path.join(" -> ")}</p>`;
                    highlightShortestPath(path);
                }

                outputHTML += `<h3>Kuyruğun Adım Adım Durumu</h3>`;
                queueStates.forEach((state, index) => {
                    outputHTML += `<p>Adım ${index + 1}: ${state.map(path => path.join(" -> ")).join(", ")}</p>`;
                });

                document.getElementById('outputText').innerHTML = outputHTML;

            }
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerHTML = `<p>Bağlantı bilgisi alınamadı! Hata: ${error.message}</p>`;
        });
}





function handleFifthIster() {
    const orcid = document.getElementById("inputForFifthIster").value;

    if (!orcid) {
        alert("5. İster için ORCID ID giriniz!");
        return;
    }

    fetch(`/get-author-info/${orcid}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('outputText').innerText = "Yazar bilgileri alınamadı!";
            } else {
                const outputText = `Girilen Yazar:\n` +
                    `Ad: ${data.author_name}\n` +
                    `ID: ${orcid}\n` +
                    `Ortak Yazar Sayısı: ${data.coauthors_count}`;
                document.getElementById('outputText').innerText = outputText;

                const outputElement = document.getElementById('outputText');
                outputElement.style.opacity = 0; 
                outputElement.style.animation = 'none'; 
                outputElement.offsetHeight; 
                outputElement.style.animation = 'fadeInText 5s forwards';
            }
            selectNodeAndHighlight(orcid);
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerText = "Yazar bilgileri alınamadı!";
        });
}




function showMostConnectedAuthor() {
    fetch("/most-connected-author")
        .then(response => response.json())
        .then(data => {
            const outputText = `En Fazla Bağlantıya Sahip Yazar:\n` +
                `Ad: ${data.author_name}\n` +
                `ID: ${data.author_id}\n` +
                `Bağlantı Sayısı: ${data.connections}`;
            document.getElementById('outputText').innerText = outputText;

            const outputElement = document.getElementById('outputText');
            outputElement.style.opacity = 0; 
            outputElement.style.animation = 'none'; 
            outputElement.offsetHeight;
            outputElement.style.animation = 'fadeInText 5s forwards'; 

            selectNodeAndHighlight(data.author_id); 
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerText = "En fazla bağlantıya sahip yazar bilgisi alınamadı!";
        });
}





function handleLongestPath() {
    const orcid = document.getElementById("inputForLongestPath").value;

    if (!orcid) {
        alert("Lütfen bir ORCID ID giriniz!");
        return;
    }

    fetch(`/longest-path/${orcid}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Yazar bilgisi alınamadı!");
            }
            return response.json();
        })
        .then(data => {
            console.log("Gelen Veri:", data);

            if (data.error) {
                document.getElementById('outputText').innerHTML = `<p>${data.error}</p>`;
            } else {
                const output = `<p>${data.message}</p>`;
                document.getElementById('outputText').innerHTML = output;
            }
            selectNodeAndHighlight(orcid);
        })
        .catch(error => {
            console.error("Hata:", error);
            document.getElementById('outputText').innerHTML = `<p>Bir hata oluştu: ${error.message}</p>`;
        });
}




var previouslyHighlightedNodes = new Set();
var previouslyHighlightedEdges = new Set(); 

function resetHighlights() {
    var originalColor = network.body.data.nodes.get(previouslySelectedNode).originalColor;
    previouslyHighlightedNodes.forEach(function (nodeId) {
        network.body.data.nodes.update({ id: nodeId, color: originalColor }); 
    });

    previouslyHighlightedEdges.forEach(function (edgeId) {
        network.body.data.edges.update({ 
            id: edgeId, 
            color: "black",
            width: 6
        });
    });

    previouslyHighlightedNodes.clear();
    previouslyHighlightedEdges.clear();
}

function highlightShortestPath(shortestPath) {
    var nodesToHighlight = [];
    var edgesToHighlight = [];

    for (let i = 0; i < shortestPath.length; i++) {
        let currentNode = shortestPath[i];

        nodesToHighlight.push(currentNode);
        previouslyHighlightedNodes.add(currentNode); 

        if (i < shortestPath.length - 1) {
            let fromNode = shortestPath[i];
            let toNode = shortestPath[i + 1];

            edges.forEach(function (edge) {
                if (
                    (edge.from === fromNode && edge.to === toNode) || 
                    (edge.from === toNode && edge.to === fromNode)
                ) {
                    edgesToHighlight.push(edge.id);
                    previouslyHighlightedEdges.add(edge.id); 
                }
            });
        }
    }

    nodesToHighlight.forEach(function (nodeId) {
        network.body.data.nodes.update({ id: nodeId, color: "yellow" });
    });

    edgesToHighlight.forEach(function (edgeId) {
        network.body.data.edges.update({ 
            id: edgeId, 
            color: "red", 
            width: 150 
        });
    });
}



var previouslySelectedNode = null; 

function selectNodeAndHighlight(nodeId) {
    if (previouslySelectedNode === nodeId) {
        return; 
    }
    if (previouslySelectedNode !== null) {
        var originalColor = network.body.data.nodes.get(previouslySelectedNode).originalColor;
        network.body.data.nodes.update({ id: previouslySelectedNode, color: originalColor });

        edges.forEach(function (edge) {
            if (edge.from === previouslySelectedNode || edge.to === previouslySelectedNode) {
                var edgeOriginalColor = edge.weight > 1 ? "yellow" : "#018786";
                network.body.data.edges.update({ 
                    id: edge.id, 
                    color: edgeOriginalColor, 
                    width: 2 
                });

                var connectedNode = edge.from === previouslySelectedNode ? edge.to : edge.from;
                var connectedOriginalColor = network.body.data.nodes.get(connectedNode).originalColor;
                network.body.data.nodes.update({ id: connectedNode, color: connectedOriginalColor });
            }
        });
    }

    edges.forEach(function (edge) {
        if (edge.from === nodeId || edge.to === nodeId) {
            network.body.data.edges.update({ 
                id: edge.id, 
                color: "red", 
                width: 150 
            });

            var connectedNode = edge.from === nodeId ? edge.to : edge.from;
            network.body.data.nodes.update({ id: connectedNode, color: "white" });
        }
    });

    network.body.data.nodes.update({ id: nodeId, color: "yellow" });
    previouslySelectedNode = nodeId;
}







function updateQueueDisplay() {
    let output = `Kuyruk Durumu:\n`;
    currentQueue.forEach((author, index) => {
        output += `${index + 1}. ${author.name} (ID: ${author.orcid}, Makale Sayısı: ${author.articles})\n`;
    });
    document.getElementById('outputText').innerText = output;

    const outputText = document.getElementById('outputText');
    outputText.style.opacity = 0;
    outputText.style.animation = 'none';
    outputText.offsetHeight;
    outputText.style.animation = 'fadeInText 5s forwards';
}




   function clearOutput() {
    const outputText = document.getElementById('outputText');
    outputText.style.opacity = 0;
    outputText.innerText = '';

    outputText.style.animation = 'none'; 
    outputText.offsetHeight; 
    outputText.style.animation = 'fadeInText 5s forwards'; 
}



function generateTreeHTML(bstData) {
    class TreeNode {
        constructor(orcid, name, weight) {
            this.orcid = orcid;
            this.name = name;
            this.weight = weight;
            this.left = null;
            this.right = null;
        }
    }

    function buildBalancedTree(data) {
        if (data.length === 0) return null;

        const midIndex = Math.floor(data.length / 2);
        const midAuthor = data[midIndex];

        const node = new TreeNode(midAuthor.orcid, midAuthor.name, midAuthor.weight);

        node.left = buildBalancedTree(data.slice(0, midIndex));
        node.right = buildBalancedTree(data.slice(midIndex + 1));

        return node;
    }

    bstData.sort((a, b) => a.weight - b.weight);

    const bstRoot = buildBalancedTree(bstData);

    function renderTree(node) {
        if (!node) return '';
        return `
            <div class="node">
                <div>
                    <strong>${node.name}</strong><br>
                    <small>ID: ${node.orcid}</small><br>
                    <small>Makale Sayısı: ${node.weight}</small>
                </div>
                <div class="connector"></div>
                <div style="display: flex; justify-content: center;">
                    ${renderTree(node.left)}
                    ${renderTree(node.right)}
                </div>
            </div>
        `;
    }

    return `
        <div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">
            ${renderTree(bstRoot)}
        </div>
    `;
}



</script>


<style>
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
    animation: fadeIn 7s forwards;  
}

.output-container:hover {
    box-shadow: 0px 20px 40px rgba(0, 0, 0, 0.3);
}

#outputText {
    font-size: 18px;
    color: #444;
    line-height: 1.6;
    word-wrap: break-word;
    overflow-wrap: break-word;
    opacity: 0;
    animation: fadeInText 7s forwards; 
}

.ister-button {
    display: inline-block;
    width: 160px;
    height: 60px;
    margin: 10px auto;
    padding: 15px;
    background-color: #018786;
    color: white;
    border: none;
    text-align: center;
    border-radius: 5px;
    font-size: 20px; 
    cursor: pointer;
    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.3);
    transition: background-color 0.3s ease, transform 0.2s ease;
}

.ister-button:hover {
    background-color: #005f63;
    transform: translateY(-3px);
}

.ister-container {
    position: fixed;
    top: 6%;
    right: 10px;
    width: 220px;
    height: 85%;
    overflow-y: auto;
    background-color: #f8f9fa;
    border: 1px solid #ddd;
    padding: 20px; 
    border-radius: 15px;
    box-shadow: 0px 8px 12px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    animation: fadeIn 7s forwards;
}

.input-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 10px;
    width: 90%; 
}

.input-container input {
    width: 90%; 
    padding: 10px;
    font-size: 16px; 
    border-radius: 5px;
    border: 1px solid #ccc;
    box-sizing: border-box;
}

.input-container button {
    width: 90%; 
    height: 45px;
    font-size: 16px;
}

.small-button {
    font-size: 16px;
    padding: 8px; 
    margin-top: 10px;
    background-color: #027a73;
    width: 90%;
}

.small-button:hover {
    background-color: #005f63;
}

@keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

@keyframes fadeInText {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

.legend-bar {
    position: fixed;
    bottom: 0;
    right: 0;
    width: 100%;
    background-color: rgba(255, 255, 255, 0.9);
    padding: 10px 20px;
    border-top: 1px solid #ccc;
    display: flex;
    justify-content: center; 
    align-items: center;
    gap: 20px;
    z-index: 1000;
    box-shadow: 0px -2px 5px rgba(0, 0, 0, 0.2);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    width: 100%; 
    height: 80px; 
    padding-left: 135px; 
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 10px; 
}

.legend-circle {
    width: 15px;
    height: 15px;
    border-radius: 50%;
    border: 1px solid #ccc;
}

.legend-line {
    display: inline-block;
    width: 30px; 
    height: 3px; 
    border-radius: 2px;
}

.legend-line {
    display: inline-block;
    width: 30px; 
    height: 3px; 
    border-radius: 2px; 
}

.legend-line {
    display: inline-block;
    width: 30px; 
    height: 3px; 
    border-radius: 2px; 
}

.ister-label {
    font-weight: bold; 
    font-size: 16px;
    margin-bottom: 5px;
    display: block;
    color: #018786;
    text-align: left; 
}

 .node {
        display: inline-block;
        margin: 10px;
        text-align: center;
    }
    .connector {
        display: block;
        height: 20px;
        width: 2px;
        margin: 0 auto;
        background-color: #ccc;
    }

</style>

<div class="output-container" id="outputContainer">
    <h3>Çıktı:</h3>
    <p id="outputText">Çıktı burada görünecek...</p>
</div>

<div class="ister-container">

    <div class="input-container">
        <label class="ister-label">1. İster</label>
        <input type="text" id="inputForFirstIster1" placeholder="1. Yazar ORCID ID">
        <input type="text" id="inputForFirstIster2" placeholder="2. Yazar ORCID ID">
        <button class="ister-button small-button" onclick="handleShortestPath()">Göster</button>
    </div>

    <div class="input-container">
        <label class="ister-label">2. İster</label>
        <input type="text" id="authorIdInput" placeholder="2.İster için Yazar ID'si giriniz">
        <button class="ister-button small-button" onclick="showQueueForAuthor()">Göster</button>
    </div>

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


<label class="ister-label">3. İster</label>
<button class="ister-button small-button" onclick="createBST()">BST Oluştur ve Göster</button>
<div id="outputText" style="margin-top: 20px;"></div>

<div class="input-container">
    <input type="text" id="orcidInput" placeholder="ORCID ID giriniz">
    <button class="ister-button small-button" onclick="deleteAuthor()">Yazar Sil</button>
</div>
<div id="outputText" style="margin-top: 20px;"></div>




    <div class="input-container">
    <label class="ister-label">4. İster</label>
    <input type="text" id="inputForAWriter" placeholder="4.Ister ID giriniz">
    <button class="ister-button small-button" onclick="handleShortestPathForCollaborators()">Hesapla</button>
</div>
<div id="outputText"></div>


    <div class="input-container">
        <label class="ister-label">5. İster</label>
        <input type="text" id="inputForFifthIster" placeholder="5. İster için Yazar ID'si giriniz">
        <button class="ister-button small-button" onclick="handleFifthIster()">Göster</button>
    </div>

    <label class="ister-label">6. İster</label>
    <button class="ister-button small-button" onclick="showMostConnectedAuthor()">Hesapla</button>


    <div class="input-container">
    <label class="ister-label">7. İster</label>
        <input id="inputForLongestPath" type="text" placeholder="7. İster için ORCID ID giriniz" />
        <button class="ister-button small-button" onclick="handleLongestPath()">Hesapla</button>
    </div>

    <button class="ister-button" onclick="clearOutput()">Çıktıyı Sıfırla</button>

    <div class="legend-bar">
    <div class="legend-item">
        <div class="legend-circle" style="background-color: #87CEFA;"></div>
        <span>Düğüm Ağırlığı %30'dan Az Olan Author'lar</span>
    </div>

    <div class="legend-item">
        <div class="legend-circle" style="background-color: #007BFF;"></div>
        <span>Düğüm Ağırlığı %30-%60 Arası Olan Author'lar</span>
    </div>

    <div class="legend-item">
        <div class="legend-circle" style="background-color: #0056b3;"></div>
        <span>Düğüm Ağırlığı %60'tan Fazla Olan Author'lar</span>
    </div>

    <div class="legend-item">
        <div class="legend-circle" style="background-color: #FF80BF;"></div>
        <span>Düğüm Ağırlığı %30'dan Az Olan Coauthor'lar</span>
    </div>

     <div class="legend-item">
        <div class="legend-circle" style="background-color: #FF66B2;"></div>
        <span>Düğüm Ağırlığı %30-%60 Arası Olan Coauthor'lar</span>
    </div>

     <div class="legend-item">
        <div class="legend-circle" style="background-color: #D5006D;"></div>
        <span>Düğüm Ağırlığı %60'tan Fazla Olan Coauthor'lar</span>
    </div>

    <div class="legend-item">
        <div class="legend-circle" style="background-color: yellow; border: 1px solid #ccc;"></div>
        <span>Seçilen Düğüm</span>
    </div>
    <div class="legend-item">
        <div class="legend-circle" style="background-color: white; border: 1px solid #ccc;"></div>
        <span>Seçilen Düğüm Coauthor'ları</span>
    </div>
        <div class="legend-item">
    <div class="legend-line" style="background-color: #018786;"></div>
    <span>Kenar Ağırlığı 1 Olan Kenarlar</span>
</div>

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

with open(output_path, "r", encoding="utf-8") as file:
    html_content = file.read()

if "</body>" in html_content:
    html_content = html_content.replace("</body>", f"{custom_js}</body>")

with open(output_path, "w", encoding="utf-8") as file:
    file.write(html_content)


@app.route('/shortest-path/<orcid1>/<orcid2>', methods=['GET'])
def find_shortest_path(orcid1, orcid2):
    global visited_queue
    global shortest_path
    visited_queue = []

    orcids = {author[0] for author in author_list}
    if orcid1 not in orcids or orcid2 not in orcids:
        return jsonify({"error": "Yazarlar arasında bağlantı bulunamadı!"}), 404

    shortest_path, queue_states = bfs_shortest_path(author_list, orcid1, orcid2)

    if shortest_path:
        return jsonify({
            "shortest_path": shortest_path,
            "queue_states": queue_states,
            "visited_queue": visited_queue
        })
    else:
        return jsonify({"error": "Yazarlar arasında bağlantı bulunamadı!"}), 404


class BSTNode:
    def __init__(self, orcid, name, weight):
        self.orcid = orcid
        self.name = name
        self.weight = weight
        self.left = None
        self.right = None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, orcid, name, weight):
        if not self.root:
            self.root = BSTNode(orcid, name, weight)
        else:
            self._insert(self.root, orcid, name, weight)

    def _insert(self, node, orcid, name, weight):
        if weight < node.weight or (weight == node.weight and orcid < node.orcid):
            if node.left:
                self._insert(node.left, orcid, name, weight)
            else:
                node.left = BSTNode(orcid, name, weight)
        else:
            if node.right:
                self._insert(node.right, orcid, name, weight)
            else:
                node.right = BSTNode(orcid, name, weight)

    def inorder_traversal(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append({"orcid": node.orcid, "name": node.name, "weight": node.weight})
            self._inorder(node.right, result)

    def reset(self):
        self.root = None

    def delete(self, orcid):
        self.root = self._delete(self.root, orcid)

    def _delete(self, node, orcid):
        if not node:
            return node

        if orcid.lower() < node.orcid.lower():
            node.left = self._delete(node.left, orcid)
        elif orcid.lower() > node.orcid.lower():
            node.right = self._delete(node.right, orcid)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left

            min_node = self._min_value_node(node.right)
            node.orcid, node.name, node.weight = min_node.orcid, min_node.name, min_node.weight

            node.right = self._delete(node.right, min_node.orcid)

        return node

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current


def bfs_shortest_path(author_list, start, goal):
    queue = [[start]]
    visited = set()
    queue_states = []
    distances = {start: 0}

    while queue:
        queue_states.append([list(p) for p in queue])
        path = queue.pop(0)
        current_node = path[-1]

        if current_node == goal:
            return path, queue_states

        neighbors = next((author[3] for author in author_list if author[0] == current_node), [])

        for neighbor in neighbors:
            edge_weight = calculate_edge_weight(current_node, neighbor)

            if neighbor not in visited and edge_weight > 0:
                visited.add(neighbor)
                new_path = path + [neighbor]
                queue.append(new_path)

                new_distance = distances[current_node] + edge_weight
                if neighbor not in distances or new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance

    return None, queue_states
def calculate_edge_weight(author1, author2):
    source_articles = set(next((author[1] for author in author_list if author[0] == author1), []))
    target_articles = set(next((author[1] for author in author_list if author[0] == author2), []))
    ortak_makaleler = source_articles.intersection(target_articles)
    return len(ortak_makaleler)



@app.route("/queue-for-author/<author_id>", methods=["GET"])
def queue_for_author(author_id):
    result = kuyruk_islemleri_2Ister(author_list, author_id)
    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)
@app.route("/add-author-to-queue/<author_id>", methods=["POST"])
def add_author_to_queue(author_id):
    global kuyruk, author_list

    author = next((author for author in author_list if author[0] == author_id), None)
    if not author:
        return jsonify({"error": "Yazar bulunamadı!"}), 404

    if any(item["orcid"] == author_id for item in kuyruk):
        return jsonify({"error": f"Kuyrukta zaten {author[1]} isimli yazar mevcut!"}), 400

    new_author = {
        "orcid": author[0],
        "name": author[1],
        "articles": len(author[2]),
        "collaborators": author[3]
    }

    kuyruk.append(new_author)
    kuyruk.sort(key=lambda x: x["articles"], reverse=True)

    return jsonify({"message": f"{new_author['name']} başarıyla kuyruğa eklendi!", "queue": kuyruk})
@app.route("/remove-author-from-queue/<author_id>", methods=["POST"])
def remove_author_from_queue(author_id):
    global kuyruk, author_list

    author = next((item for item in kuyruk if item["orcid"] == author_id), None)
    if not author:
        return jsonify({"error": f"Kuyrukta {author_id} ID'li yazar bulunamadı!"}), 404

    kuyruk = [item for item in kuyruk if item["orcid"] != author_id]

    return jsonify({"message": f"{author['name']} başarıyla kuyruktan ve ana listeden çıkarıldı!", "queue": kuyruk})
kuyruk = []
def kuyruk_islemleri_2Ister(author_list, target_author_id):
    global kuyruk

    target_author = next((author for author in author_list if author[0] == target_author_id), None)

    if not target_author:
        return {"error": f"Yazar ID'si {target_author_id} bulunamadı."}

    collaborations = target_author[3]
    collaboration_data = [
        (author[0], author[1], len(author[2]))
        for author in author_list
        if author[0] in collaborations
    ]

    for i in range(len(collaboration_data)):
        for j in range(len(collaboration_data) - 1 - i):
            if collaboration_data[j][2] < collaboration_data[j + 1][2]:
                collaboration_data[j], collaboration_data[j + 1] = collaboration_data[j + 1], collaboration_data[j]

    kuyruk.clear()
    kuyruk.extend([{"orcid": author[0], "name": author[1], "articles": author[2]} for author in collaboration_data])

    return {
        "target_author": {"orcid": target_author[0], "name": target_author[1]},
        "queue": kuyruk,
    }



@app.route('/delete-author', methods=['POST'])
def delete_author():
    global shortest_path
    try:
        orcid_to_delete = request.json.get('orcid')
        if not orcid_to_delete:
            return jsonify({"error": "ORCID belirtilmedi!"}), 400

        if orcid_to_delete in shortest_path:
            shortest_path.remove(orcid_to_delete)
        else:
            return jsonify({"error": "Verilen ORCID, shortest_path içinde bulunamadı!"}), 404

        return create_bst_from_shortest_path()

    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({"error": "Bir hata oluştu. Lütfen tekrar deneyin."}), 500
bst = BST()
shortest_path = [...]
@app.route('/bst-from-shortest-path', methods=['GET'])
def create_bst_from_shortest_path():
    global bst, shortest_path, author_list

    bst.reset()

    for author_id in shortest_path:
        author_info = next((author for author in author_list if author[0] == author_id), None)
        if not author_info:
            continue
        orcid, name, weight = author_info[0], author_info[1], len(author_info[2])
        bst.insert(orcid, name, weight)

    inorder_result = bst.inorder_traversal()
    return jsonify({"inorder_bst": inorder_result})



@app.route('/shortest-path-for-collaborators/<orcid>', methods=['GET'])
def find_shortest_path_for_collaborators(orcid):
    orcids = {author[0] for author in author_list}
    if orcid not in orcids:
        return jsonify({"error": "A Yazar bulunamadı!"}), 404

    shortest_paths = {}
    queue_states = []

    for author in author_list:
        author_id = author[0]
        if author_id != orcid:
            shortest_path, states = bfs_shortest_path4(author_list, orcid, author_id)
            if shortest_path:
                shortest_paths[author_id] = shortest_path
                queue_states.extend(states)

    if not shortest_paths:
        return jsonify({"error": "A yazarı ve işbirlikçi yazarlar arasında yol bulunamadı!"}), 404

    return jsonify({
        "shortest_paths": shortest_paths,
        "queue_states": queue_states
    })
def bfs_shortest_path4(author_list, start, goal):
    queue = [[start]]
    visited = set([start])
    queue_states = []

    while queue:
        queue_states.append([list(p) for p in queue])

        path = queue.pop(0)
        current_node = path[-1]

        if current_node == goal:
            return path, queue_states

        neighbors = next((author[3] for author in author_list if author[0] == current_node), [])

        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = path + [neighbor]
                queue.append(new_path)

    return None, queue_states



@app.route('/get-author-info/<orcid>', methods=['GET'])
def get_author_info(orcid):
    author = next((author for author in author_list if author[0] == orcid), None)
    if not author:
        return jsonify({"error": "Yazar bulunamadı!"}), 404

    coauthors_count = len(author[3])
    return jsonify({
        "author_name": author[1],
        "coauthors_count": coauthors_count
    })



@app.route("/most-connected-author")
def most_connected_author():
    most_connected = en_cok_baglanti_kuran_yazar(author_list)
    return {
        "author_name": most_connected[1],
        "author_id": most_connected[0],
        "connections": len(most_connected[3]),
    }
def en_cok_baglanti_kuran_yazar(author_list):
    most_connected_author = max(author_list, key=lambda x: len(x[3]))
    return most_connected_author



@app.route('/longest-path/<orcid>', methods=['GET'])
def longest_path(orcid):
    def dfs(node, visited):
        visited.add(node)
        max_length = 0

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                length = dfs(neighbor, visited) + 1
                max_length = max(max_length, length)

        visited.remove(node)
        return max_length

    author_exists = any(author[0] == orcid for author in author_list)
    if not author_exists:
        return jsonify({"error": "Bu ID'de bir yazar yok!"}), 404

    graph = {}
    for author in author_list:
        orcid_id = author[0]
        co_authors = author[3]
        graph[orcid_id] = co_authors

    visited = set()

    longest_path_length = dfs(orcid, visited)

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
