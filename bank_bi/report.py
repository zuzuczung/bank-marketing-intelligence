"""Write the five-stage Vietnamese report from executed validation evidence."""
import json
from .config import ROOT
from .pipeline import query


def main():
    data=json.loads((ROOT/'artifacts/data-validation.json').read_text())
    charts=json.loads((ROOT/'artifacts/chart-validation.json').read_text())
    dep=json.loads((ROOT/'artifacts/deployment.json').read_text())
    t=data['totals'];rate=t['yes']/t['n']
    def table(dim):
        rows=data['groups'][dim]
        out='| Nhóm | Bản ghi | Đăng ký | Tỷ lệ |\n|---|---:|---:|---:|\n'
        for r in rows:
            out+=f'| {r["dimension"]} | {r["n"]:,} | {r["yes"]:,} | {r["yes"]/r["n"]:.2%} |\n'
        return out
    report=f'''# Bank Marketing Intelligence — Báo cáo project

Nguồn: [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing), `bank-full.csv`, DOI 10.24432/C5K306, CC BY 4.0. Ngày triển khai: 03/11/2026; đây không phải dữ liệu phát sinh ngày triển khai.

## 1. Xác định vấn đề (Problem Identification)

**Đã thực hiện:** Xây dựng phân tích mô tả về đăng ký tiền gửi sau các chiến dịch gọi điện: (1) tỷ lệ toàn bộ và theo kênh, (2) khác biệt theo nhóm tuổi/nghề/học vấn, (3) mối liên hệ giữa số lần liên hệ, kết quả chiến dịch trước và đăng ký hiện tại. Mục tiêu là xác định giả thuyết cho thử nghiệm marketing, phục vụ project học tập/portfolio.

**Bằng chứng/kết quả:** Dashboard Superset có 3 tab, {len(dep['charts'])} biểu đồ/bảng, 3 bộ lọc kênh/tháng/nghề. KPI dùng cùng grain và tái tính dưới bộ lọc. Báo cáo và data contract định nghĩa phạm vi.

**Hạn chế:** Mỗi dòng là một bản ghi nguồn về khách và lần liên hệ cuối của chiến dịch, không có mã định danh khách. Không thể chứng minh {t['n']:,} người riêng biệt, tần suất lặp theo khách, hay hiệu quả tăng thêm do gọi điện. Không có chi phí/giá trị tiền gửi để tính ROI, CPA hoặc lợi nhuận. Không có năm đầy đủ để tính MoM/YoY.

**Đề xuất bổ sung:** Thu thập campaign_id, customer_id giả danh, thời gian từng liên hệ, consent/điều kiện liên hệ, chi phí và giá trị đăng ký. Xác định rõ tiêu chí thành công cho một thử nghiệm trước khi triển khai thực tế.

## 2. Thu thập dữ liệu (Data Collection)

**Đã thực hiện:** Tải trực tiếp archive UCI, chọn đúng `bank-full.csv` gồm 16 biến đầu vào và `y`; không ghép `bank-additional-full.csv` hoặc mẫu 10%. Giữ CSV gốc trong `data/raw`, tải lại bằng CLI và ghim SHA-256.

**Bằng chứng/kết quả:** {t['n']:,} dòng, {t['yes']:,} `yes`, {t['n']-t['yes']:,} `no`; mỗi trường không có ô trống. `source-manifest.json` lưu URL, thời điểm nhận, hash; `artifacts/source-profile.json` lưu phân bố và phạm vi. Tất cả dòng đã nạp vào staging và analytics riêng.

**Hạn chế:** Dữ liệu lịch sử của một tổ chức ngân hàng Bồ Đào Nha, không đại diện khách hàng Việt Nam hoặc tình hình 2026. Có `unknown` dù không có ô trống: kênh 13.020, học vấn 1.857, nghề 288, kết quả chiến dịch trước 36.959. Thiếu năm nên biểu đồ tháng gộp nhiều năm.

**Đề xuất bổ sung:** Bổ sung dữ liệu mới cùng định nghĩa, kiểm tra thay đổi cơ cấu khách/kênh trước khi suy rộng kết quả.

## 3. Làm sạch dữ liệu (Data Cleaning)

**Đã thực hiện:** Kiểm tra schema, accepted values, kiểu integer và khoảng hợp lệ trước nạp. Chuẩn hóa categorical về chữ thường/bỏ khoảng trắng; giữ `unknown`. Dùng `source_row` làm khóa kỹ thuật; gắn cờ trùng. Chuyển `pdays=-1` thành NULL ở trường dẫn xuất, giữ sentinel gốc. Tạo nhóm tuổi/số lần liên hệ/tháng và nhãn tiếng Việt. Giữ balance âm và giá trị cao; không cắt ngoại lai tùy ý.

**Bằng chứng/kết quả:** Không có dòng trùng hoàn toàn; giữ đủ {t['n']:,} dòng. Balance -8.019 đến 102.127 EUR, tuổi 18–95, duration 0–4.918 giây, campaign 1–63. Có 8.257 bản ghi từng được liên hệ trước; kiểm tra `pdays>=0` khớp `previous>0`. {data['passed']}/{data['total']} kiểm tra dữ liệu đạt; đối soát các nhóm bằng Python đọc CSV độc lập với SQL.

**Hạn chế:** Không có khóa khách để phát hiện trùng thực thể. Giữ ngoại lai không xác nhận mọi giá trị đều chính xác. `balance` là số dư bình quân năm theo nguồn, không phải giá trị tiền gửi do chiến dịch tạo ra.

**Đề xuất bổ sung:** Có khóa giả danh và nhật ký nghiệp vụ để phân biệt bản ghi lặp, kiểm tra các giá trị cực trị với hệ thống nguồn; chỉ áp dụng chính sách loại khi có bằng chứng.

## 4. Phân tích dữ liệu (Data Analysis)

**Đã thực hiện:** Thống kê mô tả, phân nhóm và tỷ lệ có trọng số từ tử/mẫu số. Tổng tỷ lệ đăng ký = {t['yes']:,}/{t['n']:,} = **{rate:.2%}**. Số lần liên hệ trung bình = {t['contacts']:,}/{t['n']:,} = **{t['contacts']/t['n']:.2f}**; tổng campaign là chỉ báo khối lượng ghi nhận, không phải log cuộc gọi đã khử trùng. Bảng có khoảng Wilson 95% để thể hiện quy mô ảnh hưởng đến độ chính xác xấp xỉ của tỷ lệ, không phải bảo đảm suy rộng.

### Kênh liên hệ

{table('contact_label')}
Di động có tỷ lệ cao hơn điện thoại bàn trong nguồn; nhóm chưa rõ thấp hơn. Chưa kiểm soát cơ cấu khách/thời điểm nên không coi chênh lệch này là hiệu ứng của kênh.

### Nghề nghiệp

{table('job')}
`student` và `retired` có tỷ lệ mô tả cao, nhưng quy mô nhỏ hơn `management` và `blue-collar`. Phải cân nhắc đồng thời quy mô và tỷ lệ; đây không phải danh sách khách để tự động nhắm chọn.

### Số lần liên hệ trong chiến dịch

{table('contact_band')}
Tỷ lệ ở nhóm 1 lần cao hơn nhóm trên 10 lần. Một nguyên nhân có thể là khách đăng ký sớm khiến chiến dịch dừng gọi, hoặc khách khó chuyển đổi được gọi nhiều hơn; dữ liệu không phân biệt các cơ chế đó. Không suy ra giảm số lần gọi sẽ làm tăng đăng ký.

### Kết quả chiến dịch trước

{table('previous_outcome_label')}
Nhóm từng thành công có tỷ lệ cao nhưng chỉ 1.511 bản ghi; `unknown` không được tự động đồng nhất với chưa từng liên hệ. Nguồn có 5 bản ghi từng được liên hệ nhưng kết quả trước vẫn unknown.

**Bằng chứng/kết quả:** `sql/03_analysis.sql` lưu truy vấn diễn giải; `artifacts/data-validation.json` lưu đối soát nhóm. {charts['passed']}/{charts['total']} đối soát biểu đồ với SQL đạt qua toàn bộ dữ liệu, di động, tháng 5, di động × tháng 5, student × di động và lựa chọn rỗng. Tỷ lệ ở mẫu rỗng là NULL; số bản ghi/đăng ký bằng 0.

**Hạn chế:** Phân tích quan sát, các nhóm có thể khác cơ cấu và bị ảnh hưởng bởi lựa chọn khách. Khoảng Wilson giả định nhị thức và không xử lý phụ thuộc thời gian/lặp khách. Không có mô hình dự đoán; `duration` chỉ biết sau cuộc gọi, không được dùng làm đặc trưng lựa chọn khách trước gọi. Tháng gộp năm không chứng minh mùa vụ hoặc xu hướng tăng/giảm theo thời gian.

**Đề xuất bổ sung:** Có đủ dữ liệu thì kiểm soát nhiễu, kiểm định trên thời gian độc lập và thiết kế A/B test. Nếu thêm mô hình, chỉ dùng thông tin có trước thời điểm quyết định; đánh giá PR-AUC, calibration, lift và chi phí trên tập giữ lại.

## 5. Diễn giải kết quả (Data Interpretation)

**Đã thực hiện:** Tách kết quả mô tả khỏi giả thuyết hành động. Kết luận có thể dùng ngay cho project: tỷ lệ lịch sử 11,70%; tỷ lệ khác nhau theo kênh/nhóm/lịch sử; thiếu kênh là điểm chất lượng dữ liệu đáng xử lý. Dashboard cho phép kiểm tra lại các nhóm thay vì chỉ đọc một con số tổng.

**Bằng chứng/kết quả:** Tỷ lệ di động 14,92% (4.369/29.285), điện thoại bàn 13,42% (390/2.906), kết quả trước thành công 64,73% (978/1.511). Các tỷ lệ này cùng một outcome nhưng không phải phép so sánh nhân quả.

**Hạn chế:** Chưa chạy chiến dịch mới, chưa đo tăng thêm, chưa chứng minh tiết kiệm chi phí và không có kết quả kinh doanh sau triển khai. Chưa có GitHub hoặc Google Sheet nào được coi là cập nhật chỉ vì project local đã chạy.

**Đề xuất bổ sung (chưa thực hiện):** (1) Chuẩn hóa việc ghi nhận kênh, (2) dùng lịch sử chiến dịch để đặt giả thuyết thử nghiệm, (3) thử các chính sách liên hệ trên nhóm đủ điều kiện với phân bổ ngẫu nhiên, (4) quay lại bước 1 khi có chi phí/mốc thời gian để chuyển từ mô tả sang bài toán hiệu quả tăng thêm.

## Tài nguyên đã triển khai

- [Dashboard local]({dep['dashboard_url']}) — cần dịch vụ PostgreSQL/Superset chạy trên máy.
- `sql/`: staging, analytics, truy vấn diễn giải.
- `bank_bi/`: tải nguồn, kiểm tra, pipeline, Superset API, cấu hình chart, đối soát và báo cáo.
- `docs/data-contract.md`: grain, định nghĩa, cleaning và kế hoạch kiểm tra.
- `artifacts/`: dữ liệu kiểm chứng và ID tài nguyên; không chứa mật khẩu.
'''
    (ROOT/'docs/project_report.md').write_text(report)
    print('Updated docs/project_report.md from executed evidence.')


if __name__=='__main__':main()
