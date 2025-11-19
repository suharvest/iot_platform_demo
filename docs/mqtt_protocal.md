表 1 MQTT消息协议

**主题说明**：
- `{sn}` 表示设备序列号，如 `OSC001`
- `device/info` 保持不变，包含设备信息和sn
- 其他主题都包含设备序列号，格式为 `oscilloscope/{sn}/...`

|              | indicator/terminal dm --- > mqtt broker ---> osc     (indicator/terminal dm publish)  (osc subscribe) | osc --- > mqtt broker   ---> indicator/terminal dm     (osc publish)  (indicator/terminal dm subscribe) |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **设备信息** |                                                              | **topic:**   device/info  **msg:**  {     "task": "dev_info",    "type": "oscilloscope",    "manufacturer": "ZLG",    "model": "ZDS21104",     "sn": "OSC001"  }     注：每5s推送一次 |
| **复位**     | **topic:**   oscilloscope/{sn}/set  **msg:**  {     "task": "reset",     "param":{}  } | **topic:**   oscilloscope/{sn}/set_rsp  **msg:**  {     "task": "reset",     "status": "done"  } |
| **自动设置** | **topic:**   oscilloscope/{sn}/set  **msg:**  {     "task": "autosetup",     "param":{}  } | **topic:**   oscilloscope/{sn}/set_rsp  **msg:**  {     "task": "autosetup",     "status": "done"  } |
| **测量频率** | **topic:**   oscilloscope/{sn}/query  **msg:**  {     "task":"freq_meas",    "channel":1  } | **topic:**   oscilloscope/{sn}/query_rsp  **msg:**  {     "task": "freq_meas",     "channel": 1,     "value": "999.99",     "unit": "Hz"  } |
| **测**量Vpp  | **topic:**   oscilloscope/{sn}/query  **msg:**  {   "task": "vpp_meas",     "channel":1  } | **topic:**   oscilloscope/{sn}/query_rsp  **msg:**  {     "task": "vpp_meas",     "channel": 1,     "value": "3.299",     "unit": "V"  } |
| 测量最大值   | **topic:**   oscilloscope/{sn}/query  **msg:**  {   "task": "vmax_meas",     "channel":1  } | **topic:**   oscilloscope/{sn}/query_rsp  **msg:**  {     "task": "vmax_meas",     "channel": 1,     "value": "3.322",     "unit": "V"  } |

 

 