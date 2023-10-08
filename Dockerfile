FROM public.ecr.aws/lambda/python@sha256:de232952b41f9d0bea6a05d6a62b134652af61a156f2e844d22086c296a5c2d4 as build
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1135561%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:de232952b41f9d0bea6a05d6a62b134652af61a156f2e844d22086c296a5c2d4
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

# should be replaced by requirements.txt instead
RUN pip install selenium==4.13.0
RUN pip install Faker==19.6.2
RUN pip install boto3==1.28.60

COPY --from=build /opt/chrome-linux /opt/chrome
COPY --from=build /opt/chromedriver /opt/
COPY app.py ./
CMD [ "app.lambda_handler" ]