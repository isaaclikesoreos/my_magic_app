from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.contrib import messages
from django.http import Http404
from .models import *
from .forms import *
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse
from django.http import JsonResponse
class ChatroomView(LoginRequiredMixin, TemplateView):
    template_name = "a_rtchat/chat.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chatroom_name = self.kwargs.get("chatroom_name", "public-chat")
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        chat_messages = chat_group.chat_messages.all()[:30]
        form = ChatmessageCreateForm()

        other_user = None
        if chat_group.is_private:
            if self.request.user not in chat_group.members.all(): #make sure the belongs in the chat and identify other users, for 1 on 1 chat
                raise Http404()
            for member in chat_group.members.all():
                if member != self.request.user:
                    other_user = member
                    break

        if chat_group.groupchat_name:
            if self.request.user not in chat_group.members.all(): #if the person is not in the groupchat add them when they arrive
                if self.request.user.emailaddress_set.filter(verified=True).exists():
                    chat_group.members.add(self.request.user)
                else:
                    messages.warning(self.request, "You need to verify your email to join the chat!")
                    return redirect("profile-settings")

        context.update({
            "chat_messages": chat_messages,
            "form": form,
            "other_user": other_user,
            "chatroom_name": chatroom_name,
            "chat_group": chat_group,
        })
        return context

class GetOrCreateChatroomView(LoginRequiredMixin, View):
    def get(self, request, username):
        if request.user.username == username:
            return redirect("home")

        other_user = get_object_or_404(User, username=username)
        my_chatrooms = request.user.chat_groups.filter(is_private=True)

        chatroom = None
        if my_chatrooms.exists():
            for chatroom in my_chatrooms:
                if other_user in chatroom.members.all():
                    break
            else:
                chatroom = ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user, request.user)
        else:
            chatroom = ChatGroup.objects.create(is_private=True)
            chatroom.members.add(other_user, request.user)

        return redirect("chatroom", chatroom.group_name)


class CreateGroupChatView(LoginRequiredMixin, CreateView):
    model = ChatGroup
    form_class = NewGroupForm
    template_name = "a_rtchat/create_groupchat.html"

    def form_valid(self, form):
        form.instance.admin = self.request.user
        response = super().form_valid(form)
        self.object.members.add(self.request.user)  # Add the creator to the group
        return response

    def get_success_url(self):
        # Redirect to the chatroom page of the newly created group
        return reverse('chatroom', kwargs={'chatroom_name': self.object.group_name})


class EditChatroomView(LoginRequiredMixin, UpdateView):
    model = ChatGroup
    form_class = ChatRoomEditForm
    template_name = "a_rtchat/chatroom_edit.html"

    def get_object(self):
        chatroom_name = self.kwargs.get("chatroom_name")
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        if self.request.user != chat_group.admin:
            raise Http404()
        return chat_group

    def form_valid(self, form):
        chat_group = self.get_object()
        remove_members = self.request.POST.getlist("remove_members")
        for member_id in remove_members:
            member = User.objects.get(id=member_id)
            chat_group.members.remove(member)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("chatroom", kwargs={"chatroom_name": self.object.group_name})


class DeleteChatroomView(LoginRequiredMixin, DeleteView):
    model = ChatGroup
    template_name = "a_rtchat/chatroom_delete.html"
    success_url = reverse_lazy("home")

    def get_object(self):
        chatroom_name = self.kwargs.get("chatroom_name")
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        if self.request.user != chat_group.admin:
            raise Http404()
        return chat_group


class LeaveChatroomView(LoginRequiredMixin, View):
    def post(self, request, chatroom_name):
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        if request.user not in chat_group.members.all():
            raise Http404()

        chat_group.members.remove(request.user)
        messages.success(request, "You left the Chat")
        return redirect("home")

    
    
class ChatFileUploadView(LoginRequiredMixin, View):
    def post(self, request, chatroom_name):
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

        if request.htmx and request.FILES:
            file = request.FILES['file']
            message = GroupMessage.objects.create(
                file=file,
                author=request.user,
                group=chat_group,
            )

            # WebSocket notification
            channel_layer = get_channel_layer()
            event = {
                'type': 'message_handler',
                'message_id': message.id,
            }
            async_to_sync(channel_layer.group_send)(chatroom_name, event)

            # Respond with success
            return JsonResponse({"message": "File uploaded successfully"}, status=200)

        return JsonResponse({"error": "Invalid request"}, status=400)

