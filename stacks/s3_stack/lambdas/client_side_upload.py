
import requests
response ={
    "upload": {
        "url": "https://monty-cloud-images-bucket.s3.amazonaws.com/",
        "fields": {
            "Content-Type": "application/octet-stream",
            "x-amz-server-side-encryption": "AES256",
            "key": "users/123/6671d4cd-1d93-4120-abd9-6f66b175c630/sample.jpg",
            "AWSAccessKeyId": "ASIAVWCHGWWEADPZKNBR",
            "x-amz-security-token": "IQoJb3JpZ2luX2VjEI3//////////wEaCWV1LXdlc3QtMSJIMEYCIQCiySq4WVrCbtrSTMfjBbWM2ffTh6xXbcHn6xCUaWPw6AIhAPC3Os8iA8v5qGdrjLOPIh0UZeoI71Hm98EF9UDMUmdbKoADCBYQABoMMzkwOTkxMzYxNDE2IgzGzulJj0O5Hirc/LAq3QKD3STd2XZb7PecbNofmUxYTvEaTqdm/RamIHODmWy8MamI7tR8uY4gf9/qLtqLuY0CmuL3rNZPqcJAlxoAYF92iYg1EuGYt5ayIKDvRfddDnvm/OdbMSdxCkmsiA7xqwB3EldCpm5gLaBRjGy2WT4ItrGkiWtsfFjGW8gnT+E+tl6l3+3NHtcsIa0nmAD3oNoX6t59Ry+lFoEwB/ZgC4Tcad9V4ImLIkWX7mlPTUE44bNR/PlKowZl1pu1YcWHcxVJFqZ739j0TiYnRIF+3ru1V5Ox8ZK+aLtWRUYmKSn0wtLpvFxh6f0N1VkSGqclQ0jFy3X/Cv3kv5JllQmI10K71T1Hf3ftiybdRVz7uL07UHH0Z4PqfbiPtc/j105yDleTR9Z778oXZQWeltO6j/D1y1h+jzzEVZd+YS01GyNAllklI2Vs81GdLywlJReLDWL8/E6TUjhHBb0rhXalMO/fv8YGOp0B7AR7MkmR13cMAuVmejivvNpgveumDzm+Ulr9YrBKHjLDLFz/H5GmUxcA8YJsyRsfdkJ+M9G1SDalN+8J1HkjTXV4q5VNck1SBwMznAjxMLrKX2AH1JaS8VcR+lMAwvh8bkertpGREaSmpdyMmsSFJnIksQClZZX9rUxiM638bjCg7+9Fi+PBug1v+Wv0gzE3i2Og4Vh1z4MMS8JVjg==",
            "policy": "eyJleHBpcmF0aW9uIjogIjIwMjUtMDktMjFUMTI6MzU6NDBaIiwgImNvbmRpdGlvbnMiOiBbeyJDb250ZW50LVR5cGUiOiAiYXBwbGljYXRpb24vb2N0ZXQtc3RyZWFtIn0sIFsiY29udGVudC1sZW5ndGgtcmFuZ2UiLCAxLCAyMDk3MTUyMF0sIHsieC1hbXotc2VydmVyLXNpZGUtZW5jcnlwdGlvbiI6ICJBRVMyNTYifSwgeyJidWNrZXQiOiAibW9udHktY2xvdWQtaW1hZ2VzLWJ1Y2tldCJ9LCB7ImtleSI6ICJ1c2Vycy8xMjMvNjY3MWQ0Y2QtMWQ5My00MTIwLWFiZDktNmY2NmIxNzVjNjMwL3NhbXBsZS5qcGcifSwgeyJ4LWFtei1zZWN1cml0eS10b2tlbiI6ICJJUW9KYjNKcFoybHVYMlZqRUkzLy8vLy8vLy8vL3dFYUNXVjFMWGRsYzNRdE1TSklNRVlDSVFDaXlTcTRXVnJDYnRyU1RNZmpCYldNMmZmVGg2eFhiY0huNnhDVWFXUHc2QUloQVBDM09zOGlBOHY1cUdkcmpMT1BJaDBVWmVvSTcxSG05OEVGOVVETVVtZGJLb0FEQ0JZUUFCb01Nemt3T1RreE16WXhOREUySWd6R3p1bEpqME81SGlyYy9MQXEzUUtEM1NUZDJYWmI3UGVjYk5vZm1VeFlUdkVhVHFkbS9SYW1JSE9EbVd5OE1hbUk3dFI4dVk0Z2Y5L3FMdHFMdVkwQ211TDNyTlpQcWNKQWx4b0FZRjkyaVlnMUV1R1l0NWF5SUtEdlJmZGREbnZtL09kYk1TZHhDa21zaUE3eHF3QjNFbGRDcG01Z0xhQlJqR3kyV1Q0SXRyR2tpV3RzZkZqR1c4Z25UK0UrdGw2bDMrM05IdGNzSWEwbm1BRDNvTm9YNnQ1OVJ5K2xGb0V3Qi9aZ0M0VGNhZDlWNEltTElrV1g3bWxQVFVFNDRiTlIvUGxLb3dabDFwdTFZY1dIY3hWSkZxWjczOWowVGlZblJJRiszcnUxVjVPeDhaSythTHRXUlVZbUtTbjB3dExwdkZ4aDZmME4xVmtTR3FjbFEwakZ5M1gvQ3Yza3Y1SmxsUW1JMTBLNzFUMUhmM2Z0aXliZFJWejd1TDA3VUhIMFo0UHFmYmlQdGMvajEwNXlEbGVUUjlaNzc4b1haUVdlbHRPNmovRDF5MWgranp6RVZaZCtZUzAxR3lOQWxsa2xJMlZzODFHZEx5d2xKUmVMRFdMOC9FNlRVamhIQmIwcmhYYWxNTy9mdjhZR09wMEI3QVI3TWttUjEzY01BdVZtZWppdnZOcGd2ZXVtRHptK1VscjlZckJLSGpMRExGei9INUdtVXhjQThZSnN5UnNmZGtKK005RzFTRGFsTis4SjFIa2pUWFY0cTVWTmNrMVNCd016bkFqeE1McktYMkFIMUphUzhWY1IrbE1Bd3ZoOGJrZXJ0cEdSRWFTbXBkeU1tc1NGSm5Ja3NRQ2xaWlg5clV4aU02MzhiakNnNys5RmkrUEJ1ZzF2K1d2MGd6RTNpMk9nNFZoMXo0TU1TOEpWamc9PSJ9XX0=",
            "signature": "ZWhEd/5MJuknGEShXhqHkTsybKs="
        }
    },
    "imageId": "6671d4cd-1d93-4120-abd9-6f66b175c630"
}
files = {"file": open(r"D:\Learning\MontyCloud\sample.png", "rb")}
r = requests.post(response['upload']["url"], data=response['upload']["fields"], files=files)

print(r.status_code)  # 204 = success
