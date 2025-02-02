document.addEventListener('DOMContentLoaded', () => {
    // Tab switching code (as before)
    const overviewTab = document.getElementById('overview-tab');
    const listTab = document.getElementById('list-tab');
    const overviewView = document.getElementById('overview-view');
    const listView = document.getElementById('list-view');
  
    overviewTab.addEventListener('click', () => {
        overviewView.style.display = 'block';
        listView.style.display = 'none';
        overviewTab.classList.add('active');
        listTab.classList.remove('active');
    });
  
    listTab.addEventListener('click', () => {
        overviewView.style.display = 'none';
        listView.style.display = 'block';
        listTab.classList.add('active');
        overviewTab.classList.remove('active');
    });
  
    // Tooltip for card images on hover
    document.querySelectorAll('.card-name').forEach(cardItem => {
      cardItem.addEventListener('mouseenter', function(e) {
        let tooltip = document.getElementById('card-tooltip');
        if (!tooltip) {
          tooltip = document.createElement('div');
          tooltip.id = 'card-tooltip';
          document.body.appendChild(tooltip);
        }
        tooltip.innerHTML = `<img src="${this.getAttribute('data-image-url')}" alt="" style="max-width:200px; max-height:200px;">`;
        tooltip.style.display = 'block';
        tooltip.style.left = (e.pageX + 10) + 'px';
        tooltip.style.top = (e.pageY + 10) + 'px';
      });
  
      cardItem.addEventListener('mouseleave', function() {
        const tooltip = document.getElementById('card-tooltip');
        if (tooltip) {
          tooltip.style.display = 'none';
        }
      });
  
      cardItem.addEventListener('mousemove', function(e) {
        const tooltip = document.getElementById('card-tooltip');
        if (tooltip) {
          tooltip.style.left = (e.pageX + 10) + 'px';
          tooltip.style.top = (e.pageY + 10) + 'px';
        }
      });
    });
  });
  