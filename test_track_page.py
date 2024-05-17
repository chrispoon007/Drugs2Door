import pytest
from bs4 import BeautifulSoup

html_content = """
{% extends "base.html" %}

{% block content %}
<h2>Orders</h2>
<body>
    <link rel="stylesheet" href="../static/css/styles.css">
    <div class="header">
        <h1>Order Tracking</h1>
    </div>
    <div class="container">
        <h2>Track Your Order: <a href="#">P002</a></h2>
        <div class="tracking-info">
            <div>Status: In Transit</div>
            <div>Shipping By: Canada Post</div>
            <div>Tracking ID: <a href="#">TRCKG002</a></div>
            <div>Estimated Delivery Date: May 5th, 2024</div>
        </div>
        <div class="status-bar">
            <div>
                <img src="new_order.png" alt="New Order">
                <p>New Order</p>
            </div>
            <div>
                <img src="prescription_approved.png" alt="Prescription Approved">
                <p>Prescription Approved</p>
            </div>
            <div>
                <img src="in_transit.png" alt="In Transit">
                <p>In Transit</p>
            </div>
            <div>
                <img src="delivered.png" alt="Prescription Delivered">
                <p>Prescription Delivered</p>
            </div>
        </div>
        <h3>Past History</h3>
        <div class="past-history">
            <table>
                <tr>
                    <th>Date</th>
                    <th>Event</th>
                </tr>
                <tr>
                    <td>2024-05-03, 08:17 AM</td>
                    <td>Prescription uploaded, Order Placed</td>
                </tr>
                <tr>
                    <td>2024-05-03, 10:39 AM</td>
                    <td>Prescription Approved by Shoppers Drugs, Surrey Central</td>
                </tr>
                <tr>
                    <td>2024-05-04, 10:20 AM</td>
                    <td>Order Shipped, Canada Post Tracking Number <a href="#">TRCKG002</a></td>
                </tr>
            </table>
        </div>
    </div>
</body>
</html>
{% endblock %}
"""

@pytest.fixture
def soup():
    return BeautifulSoup(html_content, 'html.parser')

def test_order_info(soup):
    container = soup.find('div', class_='container')
    assert container is not None
    order_info = container.find('h2').text
    assert 'Track Your Order: ' in order_info

#First Section


def test_tracking_info(soup):
    tracking_info = soup.find('div', class_='tracking-info')
    assert tracking_info is not None
    assert 'Status: In Transit' in tracking_info.text
    assert 'Shipping By: Canada Post' in tracking_info.text
    assert 'Tracking ID: ' in tracking_info.text
    assert 'Estimated Delivery Date: May 5th, 2024' in tracking_info.text

#Second Section


def test_status_bar(soup):
    status_bar = soup.find('div', class_='status-bar')
    assert status_bar is not None
    images = status_bar.find_all('img')
    assert len(images) == 4
    assert images[0]['alt'] == 'New Order'
    assert images[1]['alt'] == 'Prescription Approved'
    assert images[2]['alt'] == 'In Transit'
    assert images[3]['alt'] == 'Prescription Delivered'

# Third Section

def test_past_history(soup):
    past_history = soup.find('div', class_='past-history')
    assert past_history is not None
    rows = past_history.find_all('tr')
    assert len(rows) == 4  # 1 header row + 3 data rows
    assert 'Prescription uploaded, Order Placed' in rows[1].text
    assert 'Prescription Approved by Shoppers Drugs, Surrey Central' in rows[2].text
    assert 'Order Shipped, Canada Post Tracking Number' in rows[3].text

# Fourth Section