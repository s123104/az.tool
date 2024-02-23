const fs = require('fs');

// 讀取 CSV 文件
fs.readFile('21st.csv', 'utf8', (err, data) => {
    if (err) {
        console.error("讀取 CSV 文件時出錯:", err);
        return;
    }
    
    // 將 CSV 數據轉換為 JSON
    const jsonData = csvToJson(data);

    // 寫入 JSON 文件
    fs.writeFile('output.json', JSON.stringify(jsonData, null, 2), (err) => {
        if (err) {
            console.error("寫入 JSON 文件時出錯:", err);
            return;
        }
        console.log("JSON 文件已成功生成！");
    });
});

// 將 CSV 轉換為 JSON 的函數
function csvToJson(csvData) {
    const lines = csvData.trim().split('\n');
    const headers = lines.shift().split(',');
    const jsonArray = [];

    lines.forEach(line => {
        const values = line.split(',');
        const obj = {};
        headers.forEach((header, index) => {
            obj[header.trim()] = values[index].trim();
        });
        jsonArray.push(obj);
    });

    return jsonArray;
}
