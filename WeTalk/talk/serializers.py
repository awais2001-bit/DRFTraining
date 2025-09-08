from rest_framework import serializers
from talk.models import User, Contact, ChatRoom, Message
from rest_framework.validators import UniqueValidator

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {
            "password": {"write_only": True}  
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
        
        
        
class ContactSerializer(serializers.ModelSerializer):
    contact_username = serializers.CharField(write_only=True)
    contact = UserSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = ('id', 'contact', 'contact_username', 'created_at')
        
    def validate_contact_username(self, value):
        try:
            contact_username = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist.")
        
        if self.context['request'].user == contact_username:
            raise serializers.ValidationError("You cannot add yourself as a contact.")
        
        return value
    
    
    def create(self, validated_data):
        request_user = self.context['request'].user
        contact_username = validated_data.pop('contact_username')

        if Contact.objects.filter(user=request_user, contact__username=contact_username).exists():
            raise serializers.ValidationError("This contact is already added.")

        try:
            contact_user = User.objects.get(username=contact_username)
        except User.DoesNotExist:
             raise serializers.ValidationError("The specified user does not exist.")

        contact = Contact.objects.create(
            user=request_user,
            contact=contact_user,  
        )

        return contact
    
    
class ChatRoomSerializer(serializers.ModelSerializer):
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = ('id', 'user1', 'user2')
        
    
    def validate(self,data):
        user1 = self.context["request"].user
        user2_id = self.initial_data.get("user2_id")

        if not user2_id:
            raise serializers.ValidationError({"user2_id": "This field is required."})

        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user2_id": "User does not exist."})

        if user1 == user2:
            raise serializers.ValidationError("You cannot start a chat with yourself.")

        u1, u2 = sorted([user1.id, user2.id])
        if ChatRoom.objects.filter(user1_id=u1, user2_id=u2).exists():
            raise serializers.ValidationError("Chatroom already exists.")

        data["user1"], data["user2"] = user1, user2
        return data
    
    def create(self, validated_data):
        chat_room = ChatRoom.objects.create(
            user1 = validated_data['user1'],
            user2 = validated_data['user2']
        )
        return chat_room
    
    
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "chat_room", "sender", "text", "time_stamp", "is_read"]
        read_only_fields = ["time_stamp", "is_read"]

    def validate(self, data):
        request_user = self.context["request"].user
        chat_room = data.get("chat_room")

        if request_user not in [chat_room.user1, chat_room.user2]:
            raise serializers.ValidationError("You are not a participant in this chatroom.")

        return data

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)