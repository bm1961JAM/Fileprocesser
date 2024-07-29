import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_page_bg_and_logo_styles():
    # Paths to your local images
    bg_img_path = "Repeating_Pattern@2x.png"
    logo_img_path = "qqvcj14m-removebg-preview.png"

    # Encode images to base64
    bg_img_base64 = get_base64_of_bin_file(bg_img_path)
    logo_img_base64 = get_base64_of_bin_file(logo_img_path)

    # CSS to style the page
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:image/png;base64,{bg_img_base64}");
    background-size: cover;
    background-position: top right;
    background-repeat: no-repeat;
    }}

    [data-testid="stSidebar"] > div:first-child {{
    background: rgba(255, 255, 255, 0); 
    }}

    [data-testid="stHeader"] {{
    background: rgba(255, 255, 255, 0);
    }}

    [data-testid="stToolbar"] {{
    right: 2rem;
    }}

    .custom-logo {{
    position: fixed;
    top: 50px;
    left: 40px; 
    transform: scale(0.50); 
    transform-origin: top left; 
    }}

    /* Set background color for tabs and other elements */
    .css-1l7r3cz {{
        background-color: black;
    }}

    .css-1d391kg {{
        background-color: black;
        color: white;
    }}
    </style>
    """

    # HTML for the logo
    logo_html = f"""
    <div class="custom-logo">
        <img src="data:image/png;base64,{logo_img_base64}" alt="Logo">
    </div>
    """

    return page_bg_img, logo_html
