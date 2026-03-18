# Research Summary: Quantum Routing + Cache cho LEO SatNet

## Abstract
Nghiên cứu này tập trung vào bài toán định tuyến trong mạng vệ tinh LEO dưới điều kiện tải động và burst traffic. Chúng tôi đề xuất một phương pháp định tuyến lượng tử mô phỏng (CTQW-based routing) kết hợp cơ chế chống lặp gói (anti-loop) và `Routing_Table_Cache` để giảm overhead quyết định. Trên kịch bản burst 600 giây (x3 lưu lượng tại `t=300–360s`) với 5 seed độc lập, Quantum+Cache đạt hiệu năng vượt trội so với baseline cổ điển: `PDR = 0.7784 ± 0.0062` so với `0.0797 ± 0.0175`, đồng thời giảm delay trung bình từ `0.2226 ± 0.0032s` xuống `0.1368 ± 0.0015s`. Overhead quyết định của quantum được giữ ở mức `29.05 ± 7.34 ms` với cache hit rate `71.67%`.

---

## 1) Bài toán đang nghiên cứu và bối cảnh

### 1.1 Bài toán
Bài toán đặt ra là thiết kế cơ chế định tuyến có khả năng:
- Chịu tải tốt khi mạng xuất hiện nghẽn cục bộ và burst traffic.
- Duy trì tỷ lệ giao gói (PDR) cao trong môi trường topology thay đổi liên tục.
- Giữ chi phí tính toán quyết định định tuyến đủ thấp để có thể vận hành online.

### 1.2 Bối cảnh thực tế
Mạng vệ tinh LEO có tính động cao do chuyển động quỹ đạo và thay đổi liên kết theo thời gian. Với chiến lược định tuyến cổ điển mang tính cục bộ/greedy, lưu lượng dễ hội tụ về các nút thắt gây nghẽn sớm (early congestion collapse), đặc biệt khi có burst traffic.

---

## 2) Giới thiệu các khái niệm chính

### 2.1 CTQW-based Routing
- Biểu diễn mạng dưới dạng đồ thị có trọng số.
- Xây Hamiltonian từ Laplacian đồ thị.
- Mô phỏng tiến hóa trạng thái để suy ra xu hướng đường đi ưu tiên toàn cục.

### 2.2 Penalty ràng buộc
Phương pháp thêm ma trận phạt để ép quyết định định tuyến tôn trọng các ràng buộc QoS:
- Delay
- Bandwidth
- Energy

### 2.3 Anti-loop runtime guard
Ở data plane, hệ thống sử dụng:
- No-backtrack / tabu window
- Giới hạn số lần thăm node
- Retry cap để tránh vòng lặp gửi lại vô hạn

### 2.4 Routing_Table_Cache
Cache LRU theo topology signature để tái sử dụng bảng định tuyến quantum ở các cửa sổ thời gian có trạng thái mạng tương đồng, giúp giảm chi phí tính toán quyết định.

---

## 3) Phân tích vấn đề và giả thuyết nghiên cứu

### 3.1 Vấn đề của baseline
- Baseline bị nghẽn sớm, duy trì PDR thấp trong hầu hết thời gian mô phỏng.
- Khi burst xảy ra, baseline không thể phục hồi đáng kể do thiếu cơ chế thích nghi toàn cục.

### 3.2 Giả thuyết
Nếu sử dụng định tuyến quantum-guided và bổ sung cache quyết định:
- PDR sẽ duy trì ở mức cao hơn đáng kể khi burst xảy ra.
- Delay đầu-cuối giảm do điều phối lưu lượng tránh nút thắt tốt hơn.
- Overhead quyết định giảm về mức thực dụng nhờ cache hit rate cao.

---

## 4) Phương pháp đề xuất

### 4.1 Pipeline phương pháp
1. Mã hóa topology + metric cạnh thành đồ thị có trọng số.
2. Tính Hamiltonian + penalty matrix.
3. Suy ra phân bố xác suất và tạo bảng định tuyến theo cost lượng tử.
4. Áp anti-loop guard trong forwarding runtime.
5. Áp `Routing_Table_Cache` để tái sử dụng quyết định giữa các vòng.

### 4.2 Thiết lập benchmark

| Hạng mục | Thiết lập |
|---|---|
| Simulator | SatSIM (event-driven) |
| Thời gian mô phỏng | 600 giây |
| Burst traffic | x3 tại `t = 300–360s` |
| Số seed | 5 (`7, 11, 13, 17, 19`) |
| So sánh | Baseline vs Quantum+Cache |
| Chỉ số | PDR, Delay, Decision Time, Cache Hit Rate, PDR theo thời gian |

---

## 5) Benchmark và kết quả

### 5.1 Kết quả tổng hợp (Burst 600s, 5 seed)

| Method | PDR ↑ | Avg Delay (s) ↓ | Decision Time (ms) ↓ | Cache Hit Rate ↑ | Arrived | Dropped |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | `0.0797 ± 0.0175` | `0.2226 ± 0.0032` | `0.00 ± 0.00` | `0.0000 ± 0.0000` | `286.8 ± 63.1` | `3311.2 ± 63.1` |
| Quantum+Cache | `0.7784 ± 0.0062` | `0.1368 ± 0.0015` | `29.05 ± 7.34` | `0.7167 ± 0.0000` | `2802.2 ± 22.2` | `796.8 ± 22.2` |

### 5.2 Chỉ số cải thiện

| Chỉ số | Giá trị |
|---|---:|
| PDR gain (Quantum/Baseline) | `9.77x` |
| Delay reduction | `38.54%` |
| Decision overhead (Quantum) | `~29.05 ms` |
| Cache hit rate | `71.67%` |

### 5.3 Phân tích theo pha thời gian

| Mode | Pre-burst cumulative PDR (`t=240–290`) | Burst window PDR (`t=300–350`) | Post-burst cumulative PDR (`t=360–420`) |
|---|---:|---:|---:|
| Baseline | `0.0682` | `0.0669` | `0.0732` |
| Quantum+Cache | `0.6359` | `0.6805` | `0.6866` |

Diễn giải:
- Baseline rơi vào trạng thái nghẽn kéo dài, không có khả năng phục hồi mạnh sau burst.
- Quantum+Cache thể hiện **graceful degradation** trong burst và duy trì chất lượng ổn định sau burst.

- **B1: Mô hình hóa mạng động** trong [satnet.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): mỗi vòng mô phỏng cập nhật vị trí vệ tinh, liên kết khả dụng, sự kiện gửi/nhận/look-up.
- **B2: Xây trọng số định tuyến có ràng buộc** trong [quantum_routing.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): từ delay, bandwidth, energy tạo đồ thị chi phí; vi phạm ngưỡng bị phạt (penalty).
- **B3: Suy luận định tuyến lượng tử (CTQW)**: tạo Hamiltonian từ Laplacian, tiến hóa trạng thái theo thời gian để suy ra xu hướng đường đi tốt toàn cục.
- **B4: Sinh routing actions**: chuyển kết quả lượng tử thành next-hop cho từng cặp nguồn-đích; fallback khi thiếu đường.
- **B5: Ổn định data-plane** ở [node.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html) + [event.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): anti-loop (tabu/no-backtrack), giới hạn revisit, retry cap, drop reason rõ ràng.
- **B6: Giảm overhead bằng cache** ở [satnet.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): nếu topology signature tương tự thì tái dùng bảng định tuyến đã tính (cache hit), không chạy lại quantum full.
- **B7: Benchmark và xuất kết quả** ở [burst_traffic_benchmark.py](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): chạy baseline vs quantum+cache, nhiều seed, xuất CSV + hero chart.

**Ý nghĩa của từng bảng kết quả**

- **Bảng tổng hợp mean±std** ([burst_traffic_600s_cached_multiseed_summary.csv](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)):
    - `pdr_mean/std`: độ tin cậy giao gói và độ ổn định theo seed.
    - `average_delay_s_mean/std`: chất lượng độ trễ đầu-cuối.
    - `average_decision_time_s_mean/std`: chi phí tính quyết định định tuyến.
    - `cache_hit_rate_mean/std`: cache có thực sự tái dùng được hay không.
    - [arrived/dropped](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): sản lượng giao thành công và thất bại.
    - [loop_avoided](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): mức độ hệ anti-loop can thiệp để tránh vòng lặp.
- **Bảng timeseries theo thời gian** ([burst_traffic_600s_cached_multiseed_timeseries.csv](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)):
    - `cumulative_pdr_mean/std`: sức khỏe hệ thống tích lũy theo thời gian.
    - `window_pdr_mean/std`: phản ứng tức thời từng cửa sổ (rất quan trọng khi vào burst).
    - `in_burst`: đánh dấu vùng tải tăng đột ngột để đọc đúng hiệu ứng.
    - `queue_depth`: áp lực hàng đợi (nghẽn).
    - `cache_hit_rate_mean`: hiệu quả cache theo thời gian.
- **Bảng non-burst 600s** ([system_metrics_loopguard_600s_summary.csv](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)):
    - Dùng làm đối chứng: tách riêng “năng lực nền” khỏi “khả năng chịu burst”.

**Tại sao phải có từng phần**

- **Mean±std đa seed**: biến kết quả từ “1 lần chạy may mắn” thành bằng chứng thực nghiệm có độ tin cậy.
- **Timeseries**: cho thấy cơ chế động “suy giảm có kiểm soát và phục hồi”, thứ mà bảng tổng hợp không thể hiện.
- **Baseline vs Quantum+Cache**: tách rõ lợi ích thuật toán và lợi ích triển khai.
- **Cache metrics + decision time**: trả lời câu hỏi “hay nhưng có chạy thực tế được không?”.

**Diễn giải ngắn bộ số hiện tại**

- Quantum+Cache vượt baseline mạnh về PDR và delay, đồng thời giữ decision overhead ở mức vài chục ms nhờ hit-rate cao.
- Baseline rơi vào nghẽn sớm; quantum thể hiện khả năng chịu burst và ổn định hậu burst.
- Kết luận khoa học hợp lý: **cải thiện đáng kể trong mô phỏng động**, không overclaim sang thời gian phần cứng QPU thật.
### 5.4 Hình kết quả chính

![Hero Chart: Burst Traffic (Mean ± 1σ)](burst_traffic_600s_cached_multiseed_hero.png)

![Seed Example: Burst Traffic with Cache](burst_traffic_600s_seed7_cached_pdr_linechart.png)

Vùng hồng trên biểu đồ là **burst window** — khoảng thời gian bạn chủ động bơm tải tăng đột biến vào mạng.

Trong setup hiện tại:

- Bắt đầu: [t = 300s](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- Kết thúc: [t = 360s](vscode-file://vscode-app/opt/visual-studio-code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- Cường độ: lưu lượng tăng `x3`

Nó được tô để người đọc nhìn ngay “đây là giai đoạn stress test”, rồi so sánh phản ứng của baseline và quantum trong đúng đoạn này (sụp, giữ ổn định, hay phục hồi sau burst).
### 5.5 Kết quả nền không-burst (tham chiếu)

| Method | PDR ↑ | Avg Delay (s) ↓ | Decision Time (s) ↓ |
|---|---:|---:|---:|
| Baseline | `0.0867 ± 0.0289` | `0.2224 ± 0.0045` | `0.0000 ± 0.0000` |
| Quantum | `0.7800 ± 0.0002` | `0.1421 ± 0.0000` | `0.1032 ± 0.0263` |

---

## 6) Kết luận
Phương pháp Quantum+Cache cho thấy hiệu quả rõ rệt trong môi trường LEO có burst traffic:
- Tăng mạnh độ tin cậy giao gói (PDR).
- Giảm đáng kể độ trễ đầu-cuối.
- Giữ overhead quyết định ở mức khả dụng nhờ cache.

Với bộ kết quả đa seed và biểu đồ variance band, kết luận có tính ổn định thống kê thay vì chỉ dựa trên một seed đơn lẻ.

---

## 7) Hạn chế và hướng phát triển

### 7.1 Hạn chế
- Kết quả dựa trên mô phỏng SatSIM, chưa đo trực tiếp latency trên phần cứng QPU thực.
- Baseline hiện tại là chính sách cổ điển không thích nghi mạnh; có thể bổ sung thêm baseline tối ưu hơn để tăng độ chặt chẽ.
- Mô hình queue/PHY vẫn là abstraction, chưa phản ánh toàn bộ hiệu ứng thực địa.

### 7.2 Hướng phát triển
- So sánh thêm với baseline deterministic mạnh hơn (ví dụ adaptive shortest-path theo thời gian thực).
- Thử nghiệm thêm nhiều cường độ burst và nhiều pattern traffic hơn.
- Nghiên cứu chiến lược cache thông minh hơn (học theo trạng thái mạng) để giảm thêm decision latency.

---

## 8) Phụ lục tái lập (Reproducibility)

### 8.1 Dữ liệu chính
- [burst_traffic_600s_cached_multiseed_summary.csv](burst_traffic_600s_cached_multiseed_summary.csv)
- [burst_traffic_600s_cached_multiseed_timeseries.csv](burst_traffic_600s_cached_multiseed_timeseries.csv)
- [system_metrics_loopguard_600s_summary.csv](system_metrics_loopguard_600s_summary.csv)

### 8.2 Lệnh chạy benchmark burst (1 seed)

```bash
python experiments/burst_traffic_benchmark.py \
	--seconds 600 \
	--seed 7 \
	--packet-interval 0.2 \
	--burst-start 300 \
	--burst-duration 60 \
	--burst-multiplier 3 \
	--output-prefix experiments/output/burst_traffic_600s_seed7_cached
```

### 8.3 Lệnh chạy đa seed

```bash
for s in 7 11 13 17 19; do
	python experiments/burst_traffic_benchmark.py \
		--seconds 600 \
		--seed "$s" \
		--packet-interval 0.2 \
		--burst-start 300 \
		--burst-duration 60 \
		--burst-multiplier 3 \
		--output-prefix experiments/output/burst_traffic_600s_seed${s}_cached
done
```


`Cache` ở đây là **Routing Table Cache**: bộ nhớ tạm giữ lại kết quả định tuyến quantum đã tính ở các vòng trước, để **không phải tính lại từ đầu mỗi lần**.

**Cụ thể nó làm gì**

- Sau khi quantum tính xong bảng next-hop cho toàn mạng, hệ thống lưu bảng đó theo một “chữ ký trạng thái mạng” (topology signature).
- Ở vòng sau, nếu trạng thái mạng tương tự, hệ thống lấy luôn bảng đã lưu (cache hit) thay vì chạy lại CTQW.
- Nếu trạng thái khác nhiều, hệ thống tính mới rồi cập nhật cache (caclạihe miss).

**Nó giải quyết vấn đề gì**

- Vấn đề chính trước đó: quantum routing cho chất lượng tốt nhưng **overhead quyết định cao** (tốn thời gian tính toán mỗi vòng).
- Cache giảm mạnh chi phí này, nên routing quantum thực dụng hơn trong runtime dài và traffic burst.
- Trong kết quả của bạn, cache hit rate ~71.67% và decision time quantum giảm xuống mức ~29 ms/vòng (thay vì cao hơn đáng kể khi không cache).

Nếu bạn muốn, mình có thể thêm luôn một sơ đồ 5 dòng vào phần summary để giải thích luồng `cache hit/miss` cho reviewer dễ hiểu.

Trường hợp một node bị hỏng thì sẽ tính toán lại mạng lưới thế nào 
``
response của các vệ tinh khác khi nhận được tín hiệu của các vệ tinh còn lại

add simulator graphic