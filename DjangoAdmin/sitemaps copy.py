import os
import re
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, parse, ElementTree
from django.conf import settings
from django.http import HttpResponse
from django.urls import get_resolver, reverse
from django.utils.translation import activate

def generate_multilingual_sitemap():
    """
    URLs.py'den dinamik olarak çoklu dil destekli tek sitemap.xml oluşturur.
    Gereksiz URL'leri filtreler.
    
    Returns:
        str: Oluşturulan sitemap.xml içeriği
    """
    # Sitemap dosya yolu
    sitemap_path = os.path.join(settings.BASE_DIR, 'sitemap.xml')
    
    # Bugünün tarihi
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Aktif dilleri al
    languages = [lang[0] for lang in settings.LANGUAGES]
    
    def collect_urls():
        """
        URL'leri toplar ve filtreler, parametreleri işleyerek ekler.
        
        Returns:
            list: Filtrelenmiş URL listesi
        """
        all_urls = set()
        
        def process_urls(urlpatterns, base_path=''):
            for pattern in urlpatterns:
                try:
                    # Admin ve debug URL'lerini atla
                    if any(x in str(pattern) for x in ['admin', 'debug', 'static', 'media']):
                        continue
                    
                    # Alt URL pattern'lerini de topla
                    if hasattr(pattern, 'url_patterns'):
                        process_urls(pattern.url_patterns)
                    
                    # Her dil için URL oluştur
                    for lang in languages:
                        activate(lang)
                        
                        # URL name varsa reverse kullan
                        if hasattr(pattern, 'name') and pattern.name:
                            try:
                                # Parametreli URL'ler için test verisi
                                test_kwargs = {}
                                if hasattr(pattern, 'pattern') and hasattr(pattern.pattern, 'regex'):
                                    # Regex'ten parametreleri çıkart
                                    param_matches = re.findall(r'<(\w+):(\w+)>', str(pattern.pattern.regex.pattern))
                                    for param_type, param_name in param_matches:
                                        # Test verisi: id için 1, slug için 'example'
                                        if param_type == 'int':
                                            test_kwargs[param_name] = 1
                                        elif param_type == 'slug':
                                            test_kwargs[param_name] = 'example'
                                        else:
                                            test_kwargs[param_name] = 'value'
                                
                                # Reverse ile URL'yi oluştur
                                url = reverse(pattern.name, kwargs=test_kwargs)
                                
                                # Fazla / karakterlerini temizle
                                clean_url = re.sub(r'^/+|/+$', '', url)
                                
                                # Boş veya çok kısa URL'leri atla
                                if len(clean_url) > 1 and clean_url != 'admin':
                                    # Her dil için URL ekle
                                    all_urls.add(f"{url}")
                            
                            except Exception as e:
                                print(f"URL işlenirken hata (name: {pattern.name}): {e}")
                
                except Exception as e:
                    print(f"URL işlenirken hata: {e}")
        
        # Ana URL pattern'lerini işle
        process_urls(get_resolver().url_patterns)
        
        return list(all_urls)
    
    # URL'leri topla
    all_urls = collect_urls()
    
    # Sitemap dosyasını kontrol et
    if os.path.exists(sitemap_path):
        # Mevcut sitemap'i oku
        try:
            tree = parse(sitemap_path)
            root = tree.getroot()
        except Exception:
            # Dosya okunamazsa yeni kök oluştur
            root = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
    else:
        # Yeni sitemap kök elemanı oluştur
        root = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
    
    # Mevcut URL'leri izle
    processed_urls = set()
    
    # Mevcut URL elementlerini kontrol et
    for url_elem in root.findall('./url'):
        loc_elem = url_elem.find('loc')
        if loc_elem is not None:
            # URL'yi site domaininden temizle
            clean_url = loc_elem.text.replace(settings.SITE_URL, '').strip('/')
            processed_urls.add(clean_url)
    
    # URL'leri ekle
    for url_path in all_urls:
        # URL'yi temizle
        clean_url = url_path.strip('/')
        
        # Eğer URL zaten işlenmediyse
        if clean_url not in processed_urls:
            # Tam URL oluştur
            full_url = f"{settings.SITE_URL}{url_path}"
            
            # Yeni URL elemanı oluştur
            url_elem = SubElement(root, 'url')
            
            # Lokasyon ekle
            loc_elem = SubElement(url_elem, 'loc')
            loc_elem.text = full_url
            
            # Son değişim tarihi ekle
            lastmod_elem = SubElement(url_elem, 'lastmod')
            lastmod_elem.text = today
            
            # Değişim sıklığı
            changefreq_elem = SubElement(url_elem, 'changefreq')
            changefreq_elem.text = 'weekly'
            
            # Öncelik
            priority_elem = SubElement(url_elem, 'priority')
            priority_elem.text = '0.7'
            
            # İşlenmiş URL'lere ekle
            processed_urls.add(clean_url)
    
    # XML ağacını oluştur
    tree = ElementTree(root)
    
    # Dosyayı kaydet
    tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
    
    # Sitemap içeriğini oku
    with open(sitemap_path, 'r', encoding='utf-8') as f:
        sitemap_content = f.read()
    
    # Konsola bilgi yazdır
    print(f"Sitemap güncellendi: {len(all_urls)} URL")
    
    return sitemap_content

# Kullanım için view örneği
def sitemap_view(request):
    sitemap_content = generate_multilingual_sitemap()
    return HttpResponse(sitemap_content, content_type='application/xml')
