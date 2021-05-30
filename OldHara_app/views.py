import os
import requests
import json
import ntpath

from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .models import Biblio, Path_Biblio, FileStore
from .forms import addfolderForm, addDOIForm

# Create your views here.

def view_home(request):
    """
    Main view.
    """
    template_name = 'index.html'

    isCreated = False
    isExist = False
    isModaladdfolder = False
    if request.method == 'POST':

        if 'nameFolder' in request.POST:
            # create a form instance and populate it with data from the request:
            form_addfolder = addfolderForm(request.POST)
            # check whether it's valid:
            if form_addfolder.is_valid():

                nameFolder = request.POST['nameFolder']
                path = str('media/') + nameFolder

                if not os.path.exists(path):
                    os.mkdir(path)

                    b = Path_Biblio(path=nameFolder)
                    b.save()

                    isCreated = True
                else:
                    isExist = True
                isModaladdfolder = True

        else:
            form_addfolder = addfolderForm()


    # if a GET (or any other method) we'll create a blank form
    else:
        form_addfolder = addfolderForm()

    refs = Biblio.objects.order_by('-created_on')
    paths = Path_Biblio.objects.order_by('path')
    folder_list = [x for x in Path_Biblio.objects.values_list('path', flat=True).distinct()]

    countFileStore = FileStore.objects.order_by('id').count()

    return render(request, template_name,{
        'refs' : refs,
        'form_addfolder' : form_addfolder,
        'paths': paths,
        'folder_list': folder_list,
        'countFileStore' : countFileStore,
        'isCreated': isCreated,
        'isExist': isExist,
        'isModaladdfolder': isModaladdfolder,
        })

def view_add_biblio(request):
    """
    View for adding file
    """
    template_name = 'add_biblio.html'

    isCreated = False
    isExist = False
    isModaladdfolder = False
    isDOICreated = False
    isDOIExist = False
    isDOInotValid = False
    if request.method == 'POST':

        if 'dropzone_folder' in request.POST: #not(request.FILES is None):
            # print(request.POST)
            # print(request.FILES)
            folder = request.POST['dropzone_folder']
            
            uploaded_file = request.FILES['file']
            c = FileStore(
                folder = Path_Biblio.objects.get(id = folder),
                file=uploaded_file, 
            )
            c.save()

            initial_path = c.file.path
            filename = ntpath.basename(c.file.name)
            c.file.name = Path_Biblio.objects.get(id = folder).path + '/' +  filename
            new_path = settings.MEDIA_ROOT + c.file.name
            os.rename(initial_path, new_path)
            c.save()

            return JsonResponse({
                'fileAdded' : True,
                'countFileStore' : int(FileStore.objects.order_by('id').count())
            })


        if 'nameFolder' in request.POST:
            # create a form instance and populate it with data from the request:
            form_addfolder = addfolderForm(request.POST)
            form_doi = addDOIForm()
            # check whether it's valid:
            if form_addfolder.is_valid():

                nameFolder = request.POST['nameFolder']
                path = str('media/') + nameFolder

                if not os.path.exists(path):
                    os.mkdir(path)

                    b = Path_Biblio(path = nameFolder)
                    b.save()

                    isCreated = True
                else:
                    isExist = True
                isModaladdfolder = True

        elif 'nameDOI' in request.POST:
            # create a form instance and populate it with data from the request:
            form_doi = addDOIForm(request.POST)
            form_addfolder = addfolderForm()

            # check whether it's valid:
            if form_doi.is_valid():
                nameDOI = str(request.POST['nameDOI']).lower()
                folder = request.POST['folder']

                print('ionsfjoifjs', folder)
                refs = Biblio.objects.all()

                for ref_i in refs:
                    refidoi = ref_i.getDOI()

                    if refidoi == nameDOI:
                        isDOIExist = True

                if not isDOIExist:
                        crossrefurl = 'https://api.crossref.org/v1/works/' + nameDOI
                        r = requests.get(crossrefurl)

                        if r.status_code == 200:
                            isDOInotValid = False
                            isDOICreated = True

                            d = json.loads(r.text)  # r.text == <class 'str'>  and d == <class 'dict'>
                            title_newentry = str(d['message']['title'][0])

                            c = Biblio(
                                title = title_newentry,
                                data = d,
                                json_payload = r.text,
                                folder = Path_Biblio.objects.get(id = folder),
                                status = 1
                            )

                            c.save()

                            # Add id to the data
                            temp = {}
                            temp["id"] = c.id
                            temp["folder"] = c.folder.path
                            temp["title"] = str(d['message']['title'][0])
                            temp["dateY"] = str(d['message']['issued']['date-parts'][0][0])
                            d["OldHara"] = temp

                            c.data = d
                            c.json_payload = json.dumps(d)
                            c.save()


                        else:
                            isDOInotValid = True

        else:
            form_addfolder = addfolderForm()
            form_doi = addDOIForm()


    # if a GET (or any other method) we'll create a blank form
    else:
        form_addfolder = addfolderForm()
        form_doi = addDOIForm()

    refs = Biblio.objects.order_by('-created_on')
    paths = Path_Biblio.objects.order_by('path')
    folder_list = [x for x in Path_Biblio.objects.values_list('path', flat=True).distinct()]

    countFileStore = FileStore.objects.order_by('id').count()

    return render(request, template_name,{
        'refs' : refs,
        'form_addfolder' : form_addfolder,
        'paths': paths,
        'folder_list': folder_list,
        'countFileStore' : countFileStore,
        'isCreated': isCreated,
        'isExist': isExist,
        'isModaladdfolder': isModaladdfolder,
        'form_doi': form_doi,
        'isDOICreated': isDOICreated,
        'isDOIExist': isDOIExist,
        'isDOInotValid': isDOInotValid,
        })


def view_check_biblio(request):
    """
    View for check the files
    """
    template_name = 'check_biblio.html'

    isCreated = False
    isExist = False
    isModaladdfolder = False
    if request.method == 'POST':

        if 'nameFolder' in request.POST:
            # create a form instance and populate it with data from the request:
            form_addfolder = addfolderForm(request.POST)
            form_doi = addDOIForm()
            # check whether it's valid:
            if form_addfolder.is_valid():

                nameFolder = request.POST['nameFolder']
                path = str('media/') + nameFolder

                if not os.path.exists(path):
                    os.mkdir(path)

                    b = Path_Biblio(path = nameFolder)
                    b.save()

                    isCreated = True
                else:
                    isExist = True
                isModaladdfolder = True


        else:
            form_addfolder = addfolderForm()


    # if a GET (or any other method) we'll create a blank form
    else:
        form_addfolder = addfolderForm()

    refs = Biblio.objects.order_by('-created_on')
    paths = Path_Biblio.objects.order_by('path')
    folder_list = [x for x in Path_Biblio.objects.values_list('path', flat=True).distinct()]

    file_to_sort = FileStore.objects.order_by('id')

    return render(request, template_name,{
        'refs' : refs,
        'form_addfolder' : form_addfolder,
        'paths': paths,
        'folder_list': folder_list,
        'file_to_sort' : file_to_sort,
        'isCreated': isCreated,
        'isExist': isExist,
        'isModaladdfolder': isModaladdfolder,
        })

@csrf_exempt
def modify_biblio(request):
    """
    Request AJAX to modify the biblio
    """

    ref_id = int(request.POST['id'])
    t = Biblio.objects.get(id=ref_id)

    if 'title' in request.POST:
        title = request.POST['title'].rstrip("\n")

        dico_temp = t.data["message"]
        dico_temp["title"] = [title,]
        t.data["message"] = dico_temp

        t.json_payload = json.dumps(t.data)
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

    elif 'volume' in request.POST:
        volume = request.POST['volume'].rstrip("\n")

        dico_temp = t.data["message"]
        dico_temp["volume"] = volume
        t.data["message"] = dico_temp

        t.json_payload = json.dumps(t.data)
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

    elif 'issue' in request.POST:
        issue = request.POST['issue'].rstrip("\n")

        dico_temp = t.data["message"]
        dico_temp["issue"] = issue
        t.data["message"] = dico_temp

        t.json_payload = json.dumps(t.data)
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

    elif 'page' in request.POST:
        page = request.POST['page'].rstrip("\n")

        dico_temp = t.data["message"]
        dico_temp["page"] = page
        t.data["message"] = dico_temp

        t.json_payload = json.dumps(t.data)
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

    elif 'ArtNumb' in request.POST:
        ArtNumb = request.POST['ArtNumb'].rstrip("\n")

        dico_temp = t.data["message"]
        dico_temp["article-number"] = ArtNumb
        t.data["message"] = dico_temp

        t.json_payload = json.dumps(t.data)
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

    elif 'folder' in request.POST:

        t.data["OldHara"]["folder"] = request.POST['folder']
        t.json_payload = json.dumps(t.data)
        t.folder = Path_Biblio.objects.get(path=request.POST['folder'])
        t.save()

        responseData = t.data
        return JsonResponse(responseData)

   